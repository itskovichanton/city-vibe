from dataclasses import dataclass


@dataclass
class User:
    deploys: list[Deploy] = None
    machines: dict[str, Machine] = None
