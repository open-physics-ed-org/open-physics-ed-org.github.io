import os
import yaml


def get_config_order(yaml_path="po11y.yml"):
    """
    Reads the config order from po11y.yml. Returns a list of config names in order.
    """
    if not os.path.exists(yaml_path):
        return []
    with open(yaml_path, "r") as f:
        yml = yaml.safe_load(f)
        if yml and "order" in yml and isinstance(yml["order"], list):
            return [str(x).strip() for x in yml["order"] if str(x).strip()]
        else:
            return []


def main():
    order = get_config_order()
    configs_dir = "pa11y-configs"
    all_configs = [os.path.splitext(f)[0] for f in os.listdir(configs_dir) if f.endswith(".json") and f != "wcag_logos.json"]
    all_configs_set = set(all_configs)
    order_set = set(order)

    print("Config order from po11y.yml:")
    if order:
        for i, name in enumerate(order, 1):
            status = "(OK)" if name in all_configs_set else "(MISSING)"
            print(f"{i}. {name} {status}")
    else:
        print("  (none specified)")

    # Warn about configs in po11y.yml not present in pa11y-configs
    missing = [name for name in order if name not in all_configs_set]
    if missing:
        print("\nWARNING: The following configs are listed in po11y.yml but not found in pa11y-configs:")
        for name in missing:
            print(f"  - {name}")

    # Show configs present but not listed in po11y.yml
    unlisted = [name for name in all_configs if name not in order_set]
    if unlisted:
        print("\nConfigs present in pa11y-configs but not listed in po11y.yml (will run after listed ones):")
        for name in unlisted:
            print(f"  - {name}")

if __name__ == "__main__":
    main()
