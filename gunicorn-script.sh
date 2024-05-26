[program:alanzi_finance]
    directory=/opt/alanzi/finance/backend
    command=/opt/alanzi/finance/backend/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:4005 finance.wsgi:application
    autostart=true
    autorestart=true
    stderr_logfile=/var/log/gunicorn/alanzi_finance.err.log
    stdout_logfile=/var/log/gunicorn/alanzi_finance.out.log
[group:alanzi_finance]
programs:alanzi_finance