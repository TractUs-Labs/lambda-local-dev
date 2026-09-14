email-bot-sam:    cd $BACKEND_PATH/functions/email-bot && sam local start-lambda --env-vars env.json --port 3001
email-bot-proxy:  LAMBDA_PORT=3001 PROXY_PORT=8080 python3 $DEV_PATH/proxy.py
email-bot-tunnel: cloudflared tunnel --url http://localhost:8080

template-handler-sam:    cd $BACKEND_PATH/functions/template-handler && sam local start-lambda --env-vars env.json --port 3002
template-handler-proxy:  LAMBDA_PORT=3002 PROXY_PORT=8081 python3 $DEV_PATH/proxy.py
template-handler-tunnel: cloudflared tunnel --url http://localhost:8081

generate-contract-sam:    cd $BACKEND_PATH/functions/generate-contract && sam local start-lambda --env-vars env.json --port 3003
generate-contract-proxy:  LAMBDA_PORT=3003 PROXY_PORT=8082 python3 $DEV_PATH/proxy.py
generate-contract-tunnel: cloudflared tunnel --url http://localhost:8082

send-notification-sam:    cd $BACKEND_PATH/functions/send-notification && sam local start-lambda --env-vars env.json --port 3004
send-notification-proxy:  LAMBDA_PORT=3004 PROXY_PORT=8083 python3 $DEV_PATH/proxy.py
send-notification-tunnel: cloudflared tunnel --url http://localhost:8083

utils-sam:    cd $BACKEND_PATH/functions/utils && sam local start-lambda --env-vars env.json --port 3005
utils-proxy:  LAMBDA_PORT=3005 PROXY_PORT=8084 python3 $DEV_PATH/proxy.py
utils-tunnel: cloudflared tunnel --url http://localhost:8084

metal-data-processing-sam:    cd $BACKEND_PATH/functions/metal-data-processing && sam local start-lambda --env-vars env.json --parameter-overrides EnvType=dev --port 3006
metal-data-processing-proxy:  FUNCTION_NAME=FunctionImpl LAMBDA_PORT=3006 PROXY_PORT=8085 python3 $DEV_PATH/proxy.py
metal-data-processing-tunnel: cloudflared tunnel --url http://localhost:8085

agent-core-sam:    cd $BACKEND_PATH/functions/agent-core && sam local start-lambda --env-vars env.json --parameter-overrides EnvType=dev --port 3007
agent-core-proxy:  LAMBDA_PORT=3007 PROXY_PORT=8086 python3 $DEV_PATH/proxy.py
agent-core-tunnel: cloudflared tunnel --url http://localhost:8086
