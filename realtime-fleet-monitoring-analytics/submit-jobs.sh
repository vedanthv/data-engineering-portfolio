#!/usr/bin/env sh
set -eu

# Configuration from env
JOB_DIR=${JOB_DIR:-/opt/flink/jobs}
JM_REST=${JOBMANAGER_REST:-http://jobmanager:8081}
SUBMIT_ONCE=${SUBMIT_ONCE:-true}
PAR=${FLINK_PARALLELISM:-4}
SLEEP_BETWEEN_CHECKS=${SLEEP_BETWEEN_CHECKS:-5}

echo "[submit-jobs] starting. JOB_DIR=${JOB_DIR}, JM_REST=${JM_REST}, SUBMIT_ONCE=${SUBMIT_ONCE}, PAR=${PAR}"

# wait for jobmanager REST to be available
echo "[submit-jobs] waiting for JobManager REST to be ready..."
until curl -sSf "${JM_REST}/v1/overview" >/dev/null 2>&1; do
  printf '.'
  sleep ${SLEEP_BETWEEN_CHECKS}
done
echo "\n[job-submitter] JobManager REST is ready at ${JM_REST}"

SUBMITTED_FILE=/tmp/submitted_jobs.txt
touch ${SUBMITTED_FILE}

submit_file() {
  local file="$1"
  echo "[submit-jobs] submitting ${file}"
  # Use flink CLI to submit Python job - adjust if your flink binary path differs
  # -py supports Python job submission. -p sets parallelism.
  /opt/flink/bin/flink run -p ${PAR} -py "${file}"
  if [ $? -eq 0 ]; then
    echo "${file}" >> "${SUBMITTED_FILE}"
    echo "[submit-jobs] submitted ${file} (recorded)"
  else
    echo "[submit-jobs] failed to submit ${file}"
  fi
}

# main loop
while true; do
  # find all .py files (non-recursive or recursive; here recursive)
  find "${JOB_DIR}" -type f -name '*.py' | sort | while read -r jobfile; do
    # skip if already submitted
    if grep -Fxq "${jobfile}" "${SUBMITTED_FILE}" >/dev/null 2>&1; then
      echo "[submit-jobs] already submitted: ${jobfile}"
      continue
    fi
    submit_file "${jobfile}"
    # small pause between submissions
    sleep 2
  done

  if [ "${SUBMIT_ONCE}" = "true" ]; then
    echo "[submit-jobs] SUBMIT_ONCE=true: exiting after one pass"
    exit 0
  fi

  echo "[submit-jobs] sleeping before next scan..."
  sleep 30
done
