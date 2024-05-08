import asyncio
import inspect
import json
import math
import logging
import importlib, os
from datetime import datetime
from aws_synthetics.selenium import synthetics_webdriver as webdriver, constants
from aws_synthetics.common import synthetics_logger as logger, CanaryStatus


def handler(event, context):
    return asyncio.run(handle_canary(event, context))


async def handle_canary(event, context):
    canary_result = CanaryStatus.NO_RESULT.value
    canary_error = None
    start_time = None
    reset_time = None
    setup_time = None
    launch_time = None
    try:
        # reset synthetics
        reset_time = datetime.now()
        await webdriver.reset()
        reset_time = (datetime.now() - reset_time).total_seconds() * 1000

        logger.info("Start canary")

        # setup
        setup_time = datetime.now()
        webdriver.set_event_and_context(event, context)

        # Setup for the Lambda extension
        os.makedirs("/tmp/private/synthetics", exist_ok=True)
        # There is not currently a public method to access this information.
        s3_bucket_name = webdriver._uploader.s3_upload_location["bucket"]
        s3_key_prefix = webdriver._uploader.s3_upload_location["key"]
        with open("/tmp/private/synthetics/s3-bucket-name", "w") as f:
            f.write(s3_bucket_name)
        with open("/tmp/private/synthetics/s3-key-prefix", "w") as f:
            f.write(s3_key_prefix)

        # before canary
        await webdriver.before_canary()
        setup_time = (datetime.now() - setup_time).total_seconds() * 1000

        # launch
        launch_time = datetime.now()
        launch_time = (datetime.now() - launch_time).total_seconds() * 1000
    except Exception:
        logger.exception("Error launching canary")
        launch_time = launch_time if launch_time else datetime.now()
        start_time = datetime.now()
        end_time = start_time
        launch_time = (datetime.now() - launch_time).total_seconds() * 1000
        return_value = await webdriver.after_canary(canary_result, canary_error, start_time, end_time, reset_time,
                                                    setup_time, launch_time)
        logger.info("End Canary. Result %s" % json.dumps(return_value))
        # workflow expects null to be stringified
        return_value["testRunError"] = "null" if return_value["testRunError"] is None else return_value["testRunError"]
        return_value["executionError"] = "null" if return_value["executionError"] is None else return_value["executionError"]
        return json.dumps(return_value)

    # execute user steps
    try:
        logger.info("Start executing customer steps")
        start_time = datetime.now()
        customer_canary_handler = event["customerCanaryHandlerName"]
        file_name = None
        function_name = None
        if customer_canary_handler is not None:
            # Assuming handler format: fileName.functionName
            file_name, function_name = customer_canary_handler.split(".")
            logger.info("Customer canary entry file name: %s" % file_name)
            logger.info("Customer canary entry function name: %s" % function_name)

        absolute_file_path = "/var/task/" + file_name + ".py"
        # Call customer's execution handler
        if not os.path.isfile(absolute_file_path):
            raise ModuleNotFoundError('No module named: %s' % file_name)
        spec = importlib.util.spec_from_file_location(file_name, os.path.normpath(absolute_file_path))
        customer_canary = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(customer_canary)
        logger.info("Calling customer canary: %s.%s()" % (file_name, function_name))
        handler = getattr(customer_canary, function_name)
        if inspect.iscoroutinefunction(handler):
            response = await handler(event, context)
        else:
            response = handler(event, context)
        logger.info("Customer canary response %s" % json.dumps(response))
        end_time = datetime.now()
        if webdriver.get_step_errors():
            canary_result = CanaryStatus.FAILED.value
        else:
            canary_result = CanaryStatus.PASSED.value
        logger.info("Finished executing customer steps")
    except Exception as ex:
        end_time = datetime.now()
        canary_result = CanaryStatus.FAILED.value
        canary_error = ex
        logger.exception("Canary error:")

    return_value = await webdriver.after_canary(canary_result, canary_error, start_time, end_time, reset_time, setup_time, launch_time)
    logger.info("End Canary. Result %s" % json.dumps(return_value))
    # workflow expects null to be stringified
    return_value["testRunError"] = "null" if return_value["testRunError"] is None else return_value["testRunError"]
    return_value["executionError"] = "null" if return_value["executionError"] is None else return_value["executionError"]
    return json.dumps(return_value)