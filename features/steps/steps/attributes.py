from validation_handling import gherkin_ifc, StepResult
from utils import ifc

@gherkin_ifc.step('The {representation_id} shape representation has RepresentationType "{representation_type}"')
def step_impl(context, **kwargs):
    inst = kwargs.get('inst', None)
    representation_id = kwargs.get('representation_id', None)
    representation_type = kwargs.get('representation_type', None)

    if context.step.step_type == "given":
        yield list(filter(None, list(map(lambda i: ifc.instance_getter(i, representation_id, representation_type), context.instances))))
    else:
        if ifc.instance_getter(inst, representation_id, representation_type, 1):
            yield StepResult(expected=representation_type, observed=None)