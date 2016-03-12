"Implements LinkConstraint"
from .set import ConstraintSet
from ..varkey import VarKey
from .. import SignomialsEnabled


class LinkConstraint(ConstraintSet):
    """A ConstraintSet that links duplicate variables in its constraints

    Variables with the same name are linked

    Arguments
    ---------
    constraints: iterable
        valid argument to ConstraintSet
    include_only: set
        whitelist of variable names to include
    exclude: set
        blacklist of variable names, supercedes include_only
    """
    def __init__(self, constraints, include_only=None, exclude=None):
        ConstraintSet.__init__(self, constraints)
        varkeys = self.varkeys
        linkable = set()
        for varkey in varkeys:
            if len(varkeys[varkey.name]) > 1:
                linkable.add(varkey.name)
        if include_only:
            linkable &= set(include_only)
        if exclude:
            linkable -= set(exclude)
        self.linked, self.reverselinks = {}, {}
        for name in linkable:
            vks = varkeys[name]
            descr = dict(vks[0].descr)
            descr.pop("value", None)
            descr.pop("models", None)
            descr.pop("modelnums", None)
            newvk = VarKey(**descr)
            sub, subbed_vk = None, None
            for vk in vks:
                if vk in self.substitutions:
                    if sub is None:
                        subbed_vk = vk
                        sub = self.substitutions.pop(vk)
                        self.substitutions[newvk] = sub
                    else:
                        raise ValueError("substitution conflict: could not link"
                                         " %s because %s was set to %s but"
                                         " %s was set to %s" % (
                                             newvk, subbed_vk, sub,
                                             vk, self.substitutions[vk]))
            self.linked.update(dict(zip(vks, len(vks)*[newvk])))
            self.reverselinks[newvk] = vks
        with SignomialsEnabled():  # since we're just substituting varkeys.
            self.sub(self.linked)

    def process_result(self, result):
        for k in ["constants", "variables", "freevariables", "sensitivities"]:
            resultdict = result[k]
            if k == "sensitivities":  # get ["sensitivities"]["constants"]
                resultdict = resultdict["constants"]
            for newvk, oldvks in self.reverselinks.items():
                if newvk in resultdict:
                    for vk in oldvks:
                        resultdict[vk] = resultdict[newvk]
