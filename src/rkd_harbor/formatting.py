
def prod_formatting(name) -> str:
    return "\x1B[3m\x1B[93m" + name + "\x1B[0m"


def development_formatting(name) -> str:
    return "\x1B[3m\x1B[96m" + name + "\x1B[0m"
