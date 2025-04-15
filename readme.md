## Setup

1.  Clone or download the repository.

2.  Ensure the folder structure looks like this:

    ```text
    SymbolicAIPoC/
    ├── runGraph.py
    └── SKUs/
        ├── sample1.sku
        ├── sample2.sku
        └── ... (other SKU files)
    ```

3.  Populate the `SKUs` folder:
    Each file ending in `.sku` should contain one or more lines with triples in the format:

    ```plaintext
    ("Subject", "relation", "Object")
    ```

## Usage

### Command-Line Query

You can perform either a forward or a reverse query directly from the command line.

**Forward Query (Subject-Based):**

Retrieve information where the subject is provided. For example:

```bash
python runGraph.py -subject "Hypertension" -relation "treated_by"