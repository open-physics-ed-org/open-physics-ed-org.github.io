
import os
import subprocess

def main():
    import logging
    log_dir = "log"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "build.log")
    logging.basicConfig(
        filename=log_path,
        filemode="w",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )
    configs_dir = "pa11y-configs"
    configs = [f for f in os.listdir(configs_dir) if f.endswith(".json") and f != "wcag_logos.json"]
    for config in configs:
        config_path = os.path.join(configs_dir, config)
        print(config_path)
        logging.info(f"Running accessibility checks with config: {config_path}")
        result = subprocess.run([
            "python", "oerforge/verify.py", "--all", "--config", config_path
        ], capture_output=True, text=True)
        logging.info(result.stdout)
        if result.stderr:
            logging.error(result.stderr)
        if result.returncode != 0:
            logging.error(f"Check failed for {config_path} with return code {result.returncode}")

    logging.info("Generating compliance summary page...")
    result = subprocess.run(["python", "oerforge/verify.py", "--summary"], capture_output=True, text=True)
    logging.info(result.stdout)
    if result.stderr:
        logging.error(result.stderr)
    if result.returncode == 0:
        logging.info("Compliance summary page generated at build/compliance-summary.html")
    else:
        logging.error("Failed to generate compliance summary page.")

if __name__ == "__main__":
    main()