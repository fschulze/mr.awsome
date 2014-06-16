from lazy import lazy
from mr.awsome.common import BaseInstance
from mr.awsome.config import ConfigSection


class ProxyConfigSection(ConfigSection):
    def __setitem__(self, name, value):
        ConfigSection.__setitem__(self, name, value)
        if not hasattr(self, '_proxied'):
            return
        self._proxied[name] = value

    def __delitem__(self, name):
        ConfigSection.__delitem__(self, name)
        if not hasattr(self, '_proxied'):
            return
        del self._proxied[name]


class ProxyInstance(BaseInstance):
    def __init__(self, master, sid, config, instance):
        _config = ProxyConfigSection()
        _config.update(config)
        if isinstance(instance, BaseInstance):
            self.__dict__['instance'] = instance
        else:
            self._proxied_id = instance
        BaseInstance.__init__(self, master, sid, _config)

    @lazy
    def instance(self):
        aws = self.__dict__['master'].aws
        if 'masters' not in aws.__dict__:
            raise AttributeError()
        instances = aws.instances
        if self._proxied_id not in instances:
            raise ValueError(
                "The to be proxied instance '%s' for master '%s' wasn't found." % (
                    self._proxied_id,
                    self.master.id))
        orig = instances[self._proxied_id]
        config = orig.config.copy()
        config.update(self.__dict__['config'])
        config.massagers.clear()
        instance = orig.__class__(orig.master, orig.id, config)
        self.config.update(config)
        self.config._proxied = instance.config
        return instance

    def __getattr__(self, name):
        if 'instance' not in self.__dict__ and name in frozenset(('validate_id', 'get_massagers')):
            raise AttributeError(name)
        return getattr(self.instance, name)
