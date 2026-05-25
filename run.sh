#!/usr/bin/bash

function run_server() { 
    uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 $1 
}

function run_app() { 
    uv run gradio_app/app.py $1 
}

function run_analyze() { 
    uv run pipeline_analysis.py $1 
}

function clean_results() { 
    rm -rf data/results/*
    rm -rf data/history/*
}

function clean_logs() { 
    rm -rf logs/* 
}

function clean_errors() { 
    uv run utils/clean_errors.py
}

function count_errors() {
    if [ -f "$1" ]; then
        local failed_files=$(jq '[.[] | select(.is_failed == true) | .filename]' "$1")
        local total_failed=$(jq '[.[] | select(.is_failed == true)] | length' "$1")
        local total_data=$(jq '. | length' "$1")
        local failed_percent=$(awk "BEGIN {print ($total_failed / $total_data) * 100}")
        
        if [[ "$failed_files" != "[]" ]]; then
            echo "[INFO] Failed files: $failed_files"
        fi
        
        echo "[INFO] Total 'is_failed: true': $total_failed of $total_data | ~$((total_data - total_failed)) ($failed_percent%) ($1)"
    else
        echo "[WARN] File not found: $1"
    fi
}

function deps_install() {
    if [ ! -d ".venv" ]; then
        uv venv
    fi

    local project_cfg="pyproject.toml"
    local requirements="requirements.txt"

    if [ -f "$project_cfg" ]; then
        uv sync
    else
        echo "[WARN] No $project_cfg found"
    fi

    if [ -f "$requirements" ]; then
        uv pip install -r $requirements
    else
        echo "[WARN] No $requirements found"
    fi
}

function setup_project() {
    if [ -f "pyproject.toml" ]; then
        deps_install
    else
        uv init .
        deps_install
    fi
}

declare -a ARGS=("$@")
declare -r CMD="${ARGS[0]}"
declare -a OTHERS="${ARGS[@]:1}"
declare -r SUB_ARG="${OTHERS[0]}"

case "$CMD" in
    server)
        run_server $OTHERS
        ;;
    setup)
        setup_project
        ;;
    sync)
        deps_install
        ;;
    app)
        run_app $OTHERS
        ;;
    analyze)
        case "$SUB_ARG" in
            --clean)
                clean_results
                ;;
            --fresh)
                clean_errors
                ;;
            *)
                echo "Unrecognized sub-command: $SUB_ARG"
                ;;
        esac

        run_analyze $OTHERS
        ;;
    clean)
        case "$SUB_ARG" in
            --errors)
                clean_errors
                ;;
            --logs)
                clean_logs
                ;;
            --results)
                clean_results
                ;;
            --all)
                clean_logs
                clean_results
                ;;
            *)
                echo "Unrecognized sub-command: $SUB_ARG"
                ;;
        esac
        ;;
    sum)
        count_errors data/results/checkpoint.json
        ;;
    *)
        echo "Unrecognized command: $CMD"
        ;;
esac