import errors as err
import functools
import operator
import pyparsing

from behave import *
from validation_handling import validate_step, StepOutcome

from parse_type import TypeBuilder
register_type(nested_sentences=TypeBuilder.make_enum(
    dict(map(lambda x: (x, x), ("must nest only 1",
                                "must not a list of only",
                                "is nested by only 1",
                                "is nested by a list of only")))))


@validate_step('It must be nested by {constraint} {num:d} instance(s) of {other_entity}')
def step_impl(context, inst, num, constraint, other_entity):
    stmt_to_op = {'exactly': operator.eq, "at most": operator.le}
    assert constraint in stmt_to_op
    op = stmt_to_op[constraint]

    nested_entities = [entity for rel in inst.IsNestedBy for entity in rel.RelatedObjects]
    amount_found = len([1 for i in nested_entities if i.is_a(other_entity)])
    if not op(amount_found, num):
        yield StepOutcome(context, num, amount_found)


@validate_step('It must be nested by only the following entities: {other_entities}')
def step_impl(context, inst, other_entities):
    allowed_entity_types = set(map(str.strip, other_entities.split(',')))

    nested_entities = [i for rel in inst.IsNestedBy for i in rel.RelatedObjects]
    nested_entity_types = set(i.is_a() for i in nested_entities)
    if not nested_entity_types <= allowed_entity_types:
        yield StepOutcome(context, allowed_entity_types, nested_entity_types)



@validate_step('It {fragment:nested_sentences} instance(s) of {other_entity}')
def step_impl(context, inst, fragment, other_entity):
    reltype_to_extr = {'must nest': {'attribute': 'Nests', 'object_placement': 'RelatingObject', 'error_log_txt': 'nesting'},
                       'is nested by': {'attribute': 'IsNestedBy', 'object_placement': 'RelatedObjects', 'error_log_txt': 'nested by'}}
    conditions = ['only 1', 'a list of only']

    condition = functools.reduce(operator.or_, [pyparsing.CaselessKeyword(i) for i in conditions])('condition')
    relationship_type = functools.reduce(operator.or_, [pyparsing.CaselessKeyword(i[0]) for i in reltype_to_extr.items()])('relationship_type')

    grammar = relationship_type + condition  # e.g. each entity 'is nested by(relationship_type)' 'a list of only (condition)' instance(s) of other entity
    parse = grammar.parseString(fragment)

    relationship_type = parse['relationship_type']
    condition = parse['condition']
    extr = reltype_to_extr[relationship_type]
    error_log_txt = extr['error_log_txt']


    related_entities = list(map(lambda x: getattr(x, extr['object_placement'], []), getattr(inst, extr['attribute'], [])))
    if len(related_entities):
        if isinstance(related_entities[0], tuple):
            related_entities = list(related_entities[0])  # if entity has only one IfcRelNests, convert to list
        false_elements = list(filter(lambda x: not x.is_a(other_entity), related_entities))
        correct_elements = list(filter(lambda x: x.is_a(other_entity), related_entities))

        if condition == 'only 1' and len(correct_elements) > 1:
            yield StepOutcome(context, 1, len(correct_elements))
        if condition == 'a list of only':
            if len(getattr(inst, extr['attribute'], [])) > 1:
                yield StepOutcome(context, other_entity, false_elements)
            elif len(false_elements):
                yield StepOutcome(context, other_entity, false_elements)
        if condition == 'only' and len(false_elements):
            yield StepOutcome(context, correct_elements, false_elements)
