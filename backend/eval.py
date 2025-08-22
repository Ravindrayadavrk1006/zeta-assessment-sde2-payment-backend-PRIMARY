import json
from fastapi.testclient import TestClient
from server import app

import config as settings
from app.store import store
from rich.console import Console
from rich.table import Table
from datetime import datetime

client = TestClient(app)
console = Console()

def run_evaluations():
    with open("sample_evals.json") as f:
        cases = json.load(f)

    # Create results table
    table = Table(title=f"Payment Decision Evaluation Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    table.add_column("Test Case", style="cyan")
    table.add_column("Customer", style="blue")
    table.add_column("Amount", style="yellow")
    table.add_column("Expected", style="green")
    table.add_column("Got", style="red")
    table.add_column("Result", style="bold")
    table.add_column("Description", style="italic")

    passed = 0
    for i, case in enumerate(cases, 1):
        headers = {"X-API-Key": settings.API_KEY}
        input_data = case["input"]
        customer_id = input_data["customerId"]
        
        # Make the request
        r = client.post("/payments/decide", json=input_data, headers=headers)
        response = r.json()
        decision = response["decision"]
        
        # Get customer balance for context
        balance = store.get_balance(customer_id)
        
        # Determine if test passed
        passed_test = decision == case["expected"]
        if passed_test:
            passed += 1
        
        # Add row to table
        table.add_row(
            f"#{i}",
            customer_id,
            f"${input_data['amount']:.2f} (bal: ${balance:.2f})",
            case["expected"],
            decision,
            "✅" if passed_test else "❌",
            case.get("description", "No description provided")
        )

    # Print results
    console.print(table)
    
    # Print summary
    accuracy = passed / len(cases)
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"Total Cases: {len(cases)}")
    console.print(f"Passed: {passed}")
    console.print(f"Failed: {len(cases) - passed}")
    console.print(f"Accuracy: {accuracy:.2%}")
    
    # Print color-coded accuracy assessment
    if accuracy == 1.0:
        console.print("\n[green]Perfect score! All test cases passed.[/green]")
    elif accuracy >= 0.8:
        console.print("\n[yellow]Good performance, but there's room for improvement.[/yellow]")
    else:
        console.print("\n[red]Significant issues detected. Please review failed cases.[/red]")

if __name__ == "__main__":
    run_evaluations()
