<p>
  <h3 style="font-size: 3.0em; margin: 0;">Task Lattice</h3>
  <em>Distributed Task Framework for distributing work across workers</em>
</p>

<p align="left">
  <img src="https://github.com/nicholasfelixwilliams/task-lattice/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI">
  <img src="https://img.shields.io/pypi/v/task-lattice?color=%2334D058&label=pypi%20package" alt="Package version">
  <img src="https://img.shields.io/pypi/pyversions/task-lattice.svg?color=%2334D058" alt="Supported Python versions">
  <img src="https://img.shields.io/static/v1?label=code%20style&message=ruff&color=black">
</p>

---

### 🚀 Key Features
Task Lattice's key features include:

- **Broker Support** - Following brokers are supported:
    - Solace
    - Kafka
- **Queues** - Multiple queue/priority queue support
- **Async** - Async tasks supported incl. execution in event loop
- **Customisation** - Extensive customisation of queue, worker and tasks including:
    - Automated task retry
    - Dead letter queues
    - Worker concurrency
    - Queue capacity
    - ...
- **Minimal code** - Minimal code is required to use task lattice
- **DAG support** - Supports DAG (directed acyclical graph) workflow execution
- **Monitoring** - Supports live monitoring of the queues, workers, tasks

---

### ℹ️ Installation

```sh
# Using pip
pip install task-lattice

# Using poetry
poetry add task-lattice

# Using uv
uv add task-lattice
```

---

### 📦 Dependencies

TBD

---

### 📘 How to use

TBD

---

### 📘 Logging

TBD

---

### 📘 Extensions

TBD

---

### ℹ️ License

This project is licensed under the terms of the MIT license.