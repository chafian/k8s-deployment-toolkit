.PHONY: validate cluster-test
validate:
	bash scripts/validate.sh
cluster-test:
	TEST_SPRING=1 bash scripts/cluster-test.sh
