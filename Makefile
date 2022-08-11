#
#  Copyright (c) 2021 International Business Machines
#  All rights reserved.
#
#  SPDX-License-Identifier: LGPL-3.0-or-later
#
#  Authors: anita.shekar@ibm.com, sandy.kaur@ibm.com
#

MODULE := control
SETTINGS_FILE ?= main.settings

setup: requirements.txt
	pip3 install -r requirements.txt

grpc:
	@python3 -m grpc_tools.protoc \
			--proto_path=./$(MODULE)/proto \
			--python_out=./$(MODULE)/proto \
			--grpc_python_out=./$(MODULE)/proto \
			./$(MODULE)/proto/*.proto
	@sed -E -i 's/^import.*_pb2/from . \0/' ./$(MODULE)/proto/*.py

run:
	@python3 -m $(MODULE) -s $(SETTINGS_FILE)

.PHONY: test_image
test_image:
	docker build --network=host -t test_image:latest -f Dockerfile.test .

.PHONY: tests
tests: test_image
	@docker run -it -v $${PWD}:/src -w /src -e HOME=/src \
		test_image:latest pytest tests | tee pytest.log

test: test_image
	@pytest
clean:
	rm -rf .pytest_cache __pycache__
