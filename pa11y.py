from oerforge.verify import run_pa11y_on_file

if __name__ == "__main__":
    # Example: test a single file with a config
    html_file = "build/home/index.html"
    config_file = "pa11y-config/pa11y.wcag.aaa.json"
    result = run_pa11y_on_file(html_file, config_file)
    print(result)