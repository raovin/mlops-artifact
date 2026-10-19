.PHONY: help test eval eval-config eval-fail verify clean-reports

PYTHON ?= python3
PYTHONPATH := src
REPORT ?= reports/readiness-report.json
CONFIG ?= config/readiness.example.json

help:
	@printf "MLOps readiness scaffold commands:\n"
	@printf "  make test        Run unit tests\n"
	@printf "  make eval        Run passing readiness gate and write $(REPORT)\n"
	@printf "  make eval-config Run readiness gate from $(CONFIG)\n"
	@printf "  make eval-fail   Demonstrate a blocked deployment gate with weak baseline\n"
	@printf "  make verify      Run tests, passing evals, and blocked-gate demo\n"

test:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m unittest discover -s tests -v

eval:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m mlops_readiness.runner --model rule-based --min-pass-rate 1.0 --output $(REPORT)

eval-config:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m mlops_readiness.runner --config $(CONFIG)

eval-fail:
	@set +e; \
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m mlops_readiness.runner --model echo --min-pass-rate 0.8; \
	status=$$?; \
	if [ $$status -eq 1 ]; then \
		printf "Expected blocked gate observed: exit 1.\n"; \
	else \
		printf "Unexpected exit status: %s\n" "$$status"; \
		exit 1; \
	fi

verify: test eval eval-config eval-fail

clean-reports:
	@printf "Dry run only: reports are retained. Remove manually if needed.\n"
