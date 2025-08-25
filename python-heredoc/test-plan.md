# Test Plan for Docker Compose Heredoc Python

This document provides a systematic approach to verify the key behaviors of embedding Python code in Docker Compose files using heredoc syntax.

## Setup

```bash
cd /path/to/python-heredoc
```

## Test 1: Restart Behavior (Primary Issue)

**Hypothesis**: `docker compose restart` does NOT pick up changes to embedded Python code, but `docker compose down && docker compose up` does.

### Steps:

1. **Initial State**
   ```bash
   docker compose -f docker-compose-playground.yml build
   docker compose -f docker-compose-playground.yml up -d test-service
   curl http://localhost:8090/
   ```
   Expected output: `{"message": "Test version 1", ...}`

2. **Modify Code**
   Edit `docker-compose-playground.yml`, change:
   ```python
   TEST_MESSAGE = "Test version 1"
   ```
   to:
   ```python
   TEST_MESSAGE = "Test version 2"
   ```

3. **Test Restart (Should NOT work)**
   ```bash
   docker compose -f docker-compose-playground.yml restart test-service
   curl http://localhost:8090/
   ```
   Expected: Still shows "version 1" (OLD CODE)

4. **Test Down/Up (Should work)**
   ```bash
   docker compose -f docker-compose-playground.yml down test-service
   docker compose -f docker-compose-playground.yml up -d test-service
   curl http://localhost:8090/
   ```
   Expected: Shows "version 2" (NEW CODE)

## Test 2: Indentation Sensitivity

**Hypothesis**: Python indentation errors in heredoc cause service startup failures.

### Steps:

1. **Test Working Indentation**
   ```bash
   curl http://localhost:8090/indent
   ```
   Expected: Success response

2. **Break Indentation**
   Edit the `/indent` route in `test-service`, mess up indentation:
   ```python
   @app.route("/indent")
   def indent_test():
   data = {"broken": True}  # Wrong indentation
       if True:
   nested = {"bad": "indentation"}
           data.update(nested)
   ```

3. **Test Broken Service**
   ```bash
   docker compose -f docker-compose-playground.yml down test-service
   docker compose -f docker-compose-playground.yml up -d test-service
   docker compose -f docker-compose-playground.yml logs test-service
   ```
   Expected: IndentationError in logs

## Test 3: Quote Handling

**Hypothesis**: Certain quote combinations break heredoc parsing.

### Steps:

1. **Test Working Quotes**
   ```bash
   curl http://localhost:8090/quotes
   ```
   Expected: Success response

2. **Break Quotes**
   Edit the quotes route to include problematic quotes:
   ```python
   # This will break EOF termination
   message = "This contains EOF inside the string"
   ```

3. **Test Failure**
   ```bash
   docker compose -f docker-compose-playground.yml down test-service  
   docker compose -f docker-compose-playground.yml up -d test-service
   ```
   Expected: Service fails to parse properly

## Test 4: Inline Dockerfile Verification

**Hypothesis**: The inline dockerfile builds dependencies correctly and still exhibits restart behavior.

### Steps:

1. **Verify Dependencies**
   Test that the pre-built dependencies (flask, requests) work:
   ```bash
   curl http://localhost:8090/
   ```
   Expected: Service works without additional `pip install` in the command

2. **Confirm Restart Issue Persists**
   The restart behavior should be the same as Test 1 - inline dockerfiles don't change the fundamental issue.

## Test 5: Reference Examples Validation

**Hypothesis**: All services in the main docker-compose.yml should work correctly.

### Steps:

```bash
docker compose up -d
curl http://localhost:8080/     # simple-web
curl http://localhost:8080/health
curl http://localhost:8081/events  # db-service
curl -X POST http://localhost:8081/events -H "Content-Type: application/json" -d '{"message":"test"}'
curl http://localhost:8082/     # custom-build
curl http://localhost:8082/external
docker compose logs background-worker  # Check worker output
docker compose down
```

## Success Criteria

- [ ] Restart behavior confirmed (restart fails, down/up works)
- [ ] Indentation errors properly caught and services fail gracefully
- [ ] Quote handling works for valid cases, breaks predictably for invalid cases
- [ ] Inline dockerfile builds work and exhibit same restart behavior
- [ ] All reference examples start successfully and respond correctly

## Documentation Updates

After testing, update patterns in the main `docker-compose.yml` based on any discoveries. Remove any examples that don't work reliably.