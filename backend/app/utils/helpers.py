import re


def create_donation_memo(donor_name: str, amount: float) -> str:
    """Cria memo compacto para doação (máx 28 bytes)"""
    clean_name = re.sub(r"[^a-zA-Z0-9\s]", "", donor_name).strip()

    amount_str = f"{amount:.3f}".rstrip("0").rstrip(".")

    memo = f"{clean_name}:{amount_str}"

    if len(memo.encode("ascii")) > 28:
        amount_part = f":{amount_str}"
        max_name_length = 28 - len(amount_part.encode("ascii"))

        if max_name_length > 3:
            clean_name = clean_name[:max_name_length]
            memo = f"{clean_name}:{amount_str}"
        else:
            initials = "".join([word[0] for word in clean_name.split() if word])[:3]
            memo = f"{initials}:{amount_str}"

    return memo


def validate_donation_input(donor_name: str, amount: float) -> tuple[bool, str]:
    """Valida dados de entrada para doação"""
    if not donor_name or len(donor_name.strip()) < 2:
        return False, "Nome deve ter pelo menos 2 caracteres"

    if len(donor_name.strip()) > 20:
        return False, "Nome muito longo (máx 20 caracteres)"

    if amount < 0.1:
        return False, "Doação mínima: 0.1 XLM"

    if amount > 1000:
        return False, "Doação máxima: 1000 XLM"

    return True, ""
