from oerforge.verify import run_pa11y_on_file

result = run_pa11y_on_file("build/index.html", "pa11y-configs/strict.json")

print(result)