// @ts-check

/**
 * @param {Object} params
 * @param {import("@actions/github").getOctokit extends (...a: any[]) => infer R ? R : never} params.github
 * @param {import("@actions/github").context} params.context
 * @param {typeof import("@actions/core")} params.core
 */
module.exports = async ({ github, context, core }) => {
  const pr = context.payload.pull_request;
  const ref = pr.head.sha;
  const gateName = context.workflow;

  const POLL_INTERVAL_MS = 15_000;
  const TIMEOUT_MS = 30 * 60 * 1000;
  const deadline = Date.now() + TIMEOUT_MS;

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  async function listChecks() {
    const res = await github.rest.checks.listForRef({
      owner: context.repo.owner,
      repo: context.repo.repo,
      ref,
      per_page: 100,
    });
    return res.data.check_runs;
  }

  while (true) {
    if (Date.now() > deadline) {
      core.setFailed("Timed out waiting for checks to complete (30 min).");
      break;
    }

    const checks = (await listChecks()).filter(
      (check) => check.name !== gateName,
    );

    if (checks.length === 0) {
      core.info("No other checks found yet, waiting...");
      await sleep(POLL_INTERVAL_MS);
      continue;
    }

    const unfinished = checks.filter((check) => check.status !== "completed");

    if (unfinished.length > 0) {
      core.info(
        `Waiting for ${unfinished.length} unfinished check(s): ` +
          unfinished.map((c) => c.name).join(", "),
      );
      await sleep(POLL_INTERVAL_MS);
      continue;
    }

    const failing = checks.filter((check) => {
      const conclusion = check.conclusion;
      return !["success", "neutral", "skipped"].includes(conclusion);
    });

    if (failing.length > 0) {
      core.setFailed(
        `Failing check(s): ${failing.map((c) => `${c.name} (${c.conclusion})`).join(", ")}`,
      );
    } else {
      core.info("All checks passed.");
    }

    break;
  }
};
