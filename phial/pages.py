# internal
import phial.commands
import phial.pipelines
import phial.utils

# set up logging
import phial.loggers
log = phial.loggers.get_logger(__name__)


@phial.utils.public
def page(foreach=[], command_queue=phial.commands.global_queue):
    # We allow users to write @page without the (). This permits that.
    foreach_is_func = hasattr(foreach, "__call__")

    def real_decorator(function):
        # Instead of "BuildPageCommands", we just reuse the pipeline infrastructure. This function
        # will be given as a pipeline, which in turn will call the user's page function
        # appropriately.
        def page_to_pipeline_adapter(source):
            if len(source.contents) == 0:
                source.contents = [function()]
                return source
            else:
                return source | phial.pipelines.map(function) | phial.pipelines.cout()

        # If the user decorated this page with @page instead of @page(...), foreach will be the
        # same as function. In which case we should treat foreach as empty.
        apparent_foreach = foreach
        if foreach_is_func:
            apparent_foreach = []

        command = phial.pipelines.BuildPipelineCommand(page_to_pipeline_adapter, apparent_foreach,
                                                       False)
        command_queue.enqueue(command)
        return function

    if foreach_is_func:
        return real_decorator(foreach)

    return real_decorator
