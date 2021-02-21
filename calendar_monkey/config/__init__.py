import config


def load_config(config_path):
    cfg = config.ConfigurationSet(
        config.config_from_env(prefix="CM", separator="_", lowercase_keys=True),
        config.config_from_json(config_path, read_from_file=True),
    )

    validate_config(cfg)

    return cfg


def validate_config(cfg):
    if "graph" not in cfg:
        raise Exception("graph config key not found")

    if "username" not in cfg.graph:
        raise Exception("graph.username config key not found")

    if "password" not in cfg.graph:
        raise Exception("graph.password config key not found")
