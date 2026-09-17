BACKEND_PATH ?= $(shell grep ^BACKEND_PATH .overmind.env | cut -d= -f2)

.PHONY: build-email-bot build-template-handler build-generate-contract build-send-notification build-utils build-metal-data-processing build-agent-core build-all \
        clean-email-bot clean-template-handler clean-generate-contract clean-send-notification clean-utils clean-metal-data-processing clean-agent-core clean-all

build-email-bot:
	cd $(BACKEND_PATH)/functions/email-bot && sam build --use-container

build-template-handler:
	cd $(BACKEND_PATH)/functions/template-handler && sam build --use-container

build-generate-contract:
	cd $(BACKEND_PATH)/functions/generate-contract && sam build --use-container

build-send-notification:
	cd $(BACKEND_PATH)/functions/send-notification && sam build --use-container

build-utils:
	cd $(BACKEND_PATH)/functions/utils && sam build --use-container

build-metal-data-processing:
	cd $(BACKEND_PATH)/functions/metal-data-processing && sam build --use-container

build-agent-core:
	cd $(BACKEND_PATH)/functions/agent-core && sam build --use-container

build-all:
	$(MAKE) build-email-bot build-template-handler build-generate-contract build-send-notification build-utils build-metal-data-processing build-agent-core

clean-email-bot:
	rm -rf $(BACKEND_PATH)/functions/email-bot/.aws-sam

clean-template-handler:
	rm -rf $(BACKEND_PATH)/functions/template-handler/.aws-sam

clean-generate-contract:
	rm -rf $(BACKEND_PATH)/functions/generate-contract/.aws-sam

clean-send-notification:
	rm -rf $(BACKEND_PATH)/functions/send-notification/.aws-sam

clean-utils:
	rm -rf $(BACKEND_PATH)/functions/utils/.aws-sam

clean-metal-data-processing:
	rm -rf $(BACKEND_PATH)/functions/metal-data-processing/.aws-sam

clean-agent-core:
	rm -rf $(BACKEND_PATH)/functions/agent-core/.aws-sam

clean-all:
	$(MAKE) clean-email-bot clean-template-handler clean-generate-contract clean-send-notification clean-utils clean-metal-data-processing clean-agent-core
