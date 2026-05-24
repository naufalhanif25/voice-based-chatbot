#!/usr/bin/bash
options="$@"
IFS=' ' read -r -a array <<< "$options"

run_server() { 
    uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 $1 
}

run_app() { 
    uv run gradio_app/app.py $1 
}

run_analyze() { 
    uv run pipeline_analysis.py $1 
}

clean_results() { 
    rm -rf data/results/*
    rm -rf data/history/*
}

clean_logs() { 
    rm -rf logs/* 
}

clean_errors() { 
    uv run utils/clean_errors.py
}

setup_project() {
    if [ -f "pyproject.toml" ]; then
        uv sync
    else
        uv init .
        uv sync
    fi
}

command="${array[0]}"
others="${array[@]:1}"

if [ "$command" == "server" ]; then
    run_server $others
elif [ "$command" == "setup" ]; then
    setup_project
elif [ "$command" == "app" ]; then
    run_app $others
elif [ "$command" == "analyze" ]; then
    if [ "${others[0]}" == "--clean" ]; then
        clean_results
    elif [ "${others[0]}" == "--fresh" ]; then
        clean_errors
    fi
    run_analyze $others
elif [ "$command" == "clean" ]; then
    if [ "${others[0]}" == "--errors" ]; then
        clean_errors
    elif [ "${others[0]}" == "--logs" ]; then
        clean_logs
    elif [ "${others[0]}" == "--results" ]; then
        clean_results
    elif [ "${others[0]}" == "--all" ]; then
        clean_logs
        clean_results
    fi
else
    echo "Unrecognized command: $command"
fi