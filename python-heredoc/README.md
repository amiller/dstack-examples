# Single-File Docker Compose with Heredoc Python

This repository demonstrates embedding Python code directly in Docker Compose files using heredoc syntax. Everything stays in one file while maintaining readability and functionality.

## Quick Start

```bash
# Start the service
docker compose up -d

# View logs
docker compose logs -f

# Stop services  
docker compose down
```

---

## 📋 AGENT REFERENCE - COPY THIS SECTION

This pattern embeds Python code directly in Docker Compose files using bash heredoc syntax, creating truly self-contained single-file deployments without external files.

### Critical Rules
1. **NEVER `docker compose restart`** - won't pick up code changes
2. **Use `docker compose up`** for command changes
3. **Use `docker compose up --build`** for dockerfile changes  
4. **⚠️ AVOID `$VAR` in Python** - expands using HOST environment (security risk)
5. **⚠️ AVOID single quotes `'`** - breaks heredoc parsing (printf approach available but risky)
6. **Use `os.environ.get()` for runtime values**
7. **Use `$$` for literal dollar signs**
8. **Maintain YAML indentation alignment**

### Safe Patterns
```python
# ✅ Dynamic values
home = os.environ.get("HOME", "/app")

# ✅ Literal dollars  
price = "$$19.99"  # → "$19.99"

# ✅ Paths with backslashes
path = "C:\\Program Files"

# ✅ Single quotes: avoid entirely OR use printf approach
text = "It is working"  # Safest - no quotes at all
text = "It'\''s working"  # Escape: '\'' for each '
# Advanced: printf + unquoted EOF (⚠️ enables variable expansion)
SQ=$(printf "\\047"); cat > file << EOF
message = "It${SQ}s working!"
EOF
```

### Commands
```bash
docker compose up              # Command changes
docker compose up --build     # Dockerfile changes  
docker compose logs -f        # View logs
```

### Core Pattern
```yaml
services:
  web-service:
    build:
      context: .
      dockerfile_inline: |
        FROM python:3.11-slim
        RUN pip install requests
        ENV PYTHONUNBUFFERED=1
    ports:
      - "8080:8080"
    command: |
      bash -c '
      pip install flask &&
      cat > /tmp/app.py << "EOF"
      from flask import Flask, jsonify
      import os
      
      app = Flask(__name__)
      
      @app.route("/")
      def demo():
          home = os.environ.get("HOME", "/app")
          price = "$$19.99"
          return jsonify({"home": home, "price": price})
      
      if __name__ == "__main__":
          app.run(host="0.0.0.0", port=8080)
      EOF
      python /tmp/app.py
      '
```

---

## Testing New Patterns

Use `docker-compose-playground.yml` to validate behavior:

1. **Start playground**: `docker compose -f docker-compose-playground.yml build && docker compose -f docker-compose-playground.yml up -d`

2. **Test changes**:
   - Edit the playground file
   - Try different restart methods
   - Check `http://localhost:8090/` for results

3. **Common tests**:
   - Change `TEST_MESSAGE` and test restart vs up behavior
   - Break indentation deliberately to see YAML parsing errors
   - Add problematic quotes or EOF patterns
   - Test new dependencies in dockerfile vs command

4. **Clean up**: `docker compose -f docker-compose-playground.yml down`

The playground has multiple endpoints (`/`, `/indent`, `/quotes`, `/test-deps`) designed to test different failure modes we've validated.

## Files in This Repository

- `docker-compose.yml` - Clean reference implementation
- `docker-compose-playground.yml` - Testing environment for new patterns  
- `test-plan.md` - Systematic testing methodology
- `README.md` - This guide