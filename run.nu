#!/usr/bin/env nu

def run_server [arg: string = ""] {
    uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 $arg
}

def run_app [arg: string = ""] {
    uv run gradio_app/app.py $arg
}

def run_analyze [arg: string = ""] {
    uv run pipeline_analysis.py $arg
}

def clean_results [] {
    rm -rf data/results/*
    rm -rf data/history/*
}

def clean_logs [] {
    rm -rf logs/*
}

def clean_errors [] {
    uv run utils/clean_errors.py
}

def count_errors [file_path: path] {
    if ($file_path | path exists) {
        let data = (open $file_path)
        let total_data = ($data | length)
        
        let failed_data = ($data | where is_failed == true)
        let total_failed = ($failed_data | length)
        let failed_files = ($failed_data | get filename)
        
        let failed_percent = (if $total_data > 0 { ($total_failed / $total_data) * 100 } else { 0 })
        let success_data = $total_data - $total_failed

        print $"[INFO] Failed files: ($failed_files | to json)"
        print $"[INFO] Total 'is_failed: true': ($total_failed) of ($total_data) | ~($success_data) (($failed_percent | math round -p 2)%) (($file_path))"
    } else {
        print $"[WARN] File not found: ($file_path) (skipped)"
    }
}

def setup_project [] {
    if ("pyproject.toml" | path exists) {
        uv venv
        uv sync
        uv pip install -r requirements.txt
    } else {
        uv init .
        uv venv
        uv sync
        uv pip install -r requirements.txt
    }
}

def main [command: string, ...others: string] {
    let sub_arg = (if ($others | is-empty) { "" } else { $others | get 0 })
    let full_others = ($others | str join " ")

    match $command {
        "setup" => { setup_project }
        "server" => { run_server $full_others }
        "app" => { run_app $full_others }
        "analyze" => {
            if $sub_arg == "--clean" { clean_results }
            if $sub_arg == "--fresh" { clean_errors }
            run_analyze $full_others
        }
        "clean" => {
            match $sub_arg {
                "--errors" => { clean_errors }
                "--logs" => { clean_logs }
                "--results" => { clean_results }
                "--all" => {
                    clean_logs
                    clean_results
                }
                _ => { print "Unknown clean flag" }
            }
        }
        "sum" => { count_errors data/results/checkpoint.json }
        _ => { print $"Unrecognized command: ($command)" }
    }
}