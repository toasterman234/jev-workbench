import { describe, expect, it } from "vitest";
import classifyDataType from "../examples/work-judgment/classify_data_type.json";
import nextIntent from "../examples/work-judgment/next_intent.json";
import selectArtifact from "../examples/work-judgment/select_artifact.json";
import selectPlaybook from "../examples/work-judgment/select_playbook.json";
import requiresHumanGate from "../examples/work-judgment/requires_human_gate.json";
import evidenceSatisfiesExit from "../examples/work-judgment/evidence_satisfies_exit.json";
import { evaluate, mapState, validateConfig } from "../apps/server/src/engine";

const choiceConfigs = [
  [classifyDataType, "primary_data_type", "other_needs_new"],
  [nextIntent, "next_intent", "unclear_needs_review"],
  [selectArtifact, "artifact_type", "other_needs_new"],
  [selectPlaybook, "playbook_key", "other_needs_new"],
] as const;

function choiceAnswer(config: any, questionId: string, choice: string, confidence = 0.9) {
  const keys = Object.keys(config.questions[questionId].criteria);
  const rest = keys.length > 1 ? (1 - confidence) / (keys.length - 1) : 0;
  return {
    model: config.model,
    answers: {
      [questionId]: {
        type: "choice",
        choice,
        confidence,
        probabilities: Object.fromEntries(keys.map((key) => [key, key === choice ? confidence : rest])),
      },
    },
  };
}

function noulAnswer(config: any, questionId: string, value: number) {
  return {
    model: config.model,
    answers: {
      [questionId]: {
        type: "noul",
        noul: value,
      },
    },
  };
}

describe("work judgment phase-1 configs", () => {
  it("all six configs validate with the existing v1 DSL", () => {
    for (const config of [
      classifyDataType,
      nextIntent,
      selectArtifact,
      selectPlaybook,
      requiresHumanGate,
      evidenceSatisfiesExit,
    ]) {
      expect(validateConfig(structuredClone(config))).toBeTruthy();
    }
  });

  it("optional context fields are omitted from state when absent", () => {
    expect(mapState(validateConfig(structuredClone(nextIntent)), { content: "fix it" })).toEqual({
      content: "fix it",
    });
  });

  it.each(choiceConfigs)(
    "%s preserves explicit fallback choices while marking them for review",
    (raw, questionId, fallback) => {
      const config = validateConfig(structuredClone(raw));
      const result = evaluate(config, { content: "ambiguous work" }, choiceAnswer(config, questionId, fallback));
      expect(result.status).toBe("needs_review");
      expect(Object.values(result.data)).toContain(fallback);
      expect(result.review_reasons.length).toBeGreaterThan(0);
    },
  );

  it("requires_human_gate uses Noul probability and reviews the ambiguous band", () => {
    const config = validateConfig(structuredClone(requiresHumanGate));
    expect(evaluate(config, { content: "minor reversible edit" }, noulAnswer(config, "requires_human_gate", 0.2))).toEqual({
      status: "ok",
      data: { requires_human_gate: 0.2 },
      review_reasons: [],
    });
    expect(evaluate(config, { content: "uncertain authority" }, noulAnswer(config, "requires_human_gate", 0.55)).status).toBe("needs_review");
  });

  it("evidence_satisfies_exit keeps high-confidence proof out of review and flags ambiguity", () => {
    const config = validateConfig(structuredClone(evidenceSatisfiesExit));
    expect(evaluate(config, { content: "browser verification required" }, noulAnswer(config, "evidence_satisfies_exit", 0.95))).toEqual({
      status: "ok",
      data: { evidence_satisfies_exit: 0.95 },
      review_reasons: [],
    });
    expect(evaluate(config, { content: "uncertain evidence" }, noulAnswer(config, "evidence_satisfies_exit", 0.65)).status).toBe("needs_review");
  });
});
