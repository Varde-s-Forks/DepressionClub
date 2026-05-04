// @ts-check

/**
 * @param {Object} params
 * @param {import("@actions/github").getOctokit extends (...a: any[]) => infer R ? R : never} params.github
 * @param {import("@actions/github").context} params.context
 * @param {typeof import("@actions/core")} params.core
 */
module.exports = async ({ github, context, core }) => {
  const pr = context.payload.pull_request;
  const gateName = context.job;

  if (!pr) {
    core.setFailed("No pull request found");
    return;
  }

  const ref = pr.head.sha;

  const POLL_INTERVAL_MS = 15_000;
  const TIMEOUT_MS = 60 * 60 * 1000;
  const deadline = Date.now() + TIMEOUT_MS;

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  async function listChecks() {
    const checkRuns = [];
    let page = 1;
    while (true) {
      const res = await github.rest.checks.listForRef({
        owner: context.repo.owner,
        repo: context.repo.repo,
        ref,
        per_page: 100,
        page,
      });
      checkRuns.push(...res.data.check_runs);
      if (res.data.check_runs.length < 100) break;
      page++;
    }
    return checkRuns;
  }

  const startTime = Date.now();
  const INITIAL_WAIT_MS = 2 * 60 * 1000; // Wait 2 mins for checks to start

  while (true) {
    const now = Date.now();
    if (now > deadline) {
      core.setFailed("Timed out waiting for checks to complete (60 min).");
      break;
    }

    const checks = (await listChecks()).filter(
      (check) => check.name !== gateName,
    );

    if (checks.length === 0) {
      if (now - startTime > INITIAL_WAIT_MS) {
        core.info(
          `No other checks started after 2 minutes. 
          Assuming no CI needed for this PR.`,
        );
        break;
      }
      core.info(
        `No other checks found yet. 
        Waiting up to ${Math.round((INITIAL_WAIT_MS - (now - startTime)) / 1000)}s more for checks to register...`,
      );
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
        `Failing check(s): 
        ${failing.map((c) => `${c.name} (${c.conclusion})`).join(", ")}`,
      );
    } else {
      core.info("All checks passed.");
    }

    break;
  }
};
