import re
from typing import Optional
from datetime import datetime

def extract_email(text: str) -> Optional[str]:
    if not text:
        return None
    
    text_lower = text.lower().strip()
    
    original_text = text_lower
    text_lower = re.sub(r'[.,?;:!]+$', '', text_lower)
    
    text_lower = re.sub(r'\b(at\s+)?at\s+the\s+rate\b', '@', text_lower, flags=re.IGNORECASE)
    text_lower = re.sub(r'\bat\s+rate\b', '@', text_lower)
    
    text_lower = re.sub(r'\s+at\s+', '@', text_lower)
    
    text_lower = re.sub(r'@+', '@', text_lower)
    text_lower = re.sub(r'@\s*at\s*', '@', text_lower)
    text_lower = re.sub(r'at\s*@', '@', text_lower)
    
    text_lower = re.sub(r'\bdot\b', '.', text_lower, flags=re.IGNORECASE)
    text_lower = re.sub(r'\bpoint\b', '.', text_lower, flags=re.IGNORECASE)
    
    text_lower = re.sub(r'\s*@\s*', '@', text_lower)
    text_lower = re.sub(r'\s*\.\s*', '.', text_lower)
    
    filler_words = ['the', 'is', 'my', 'yeah', 'yes', 'question mark', 'comma', 'period', 'and', 'rate']
    for word in filler_words:
        if len(word) > 1:
            text_lower = re.sub(r'\b' + word + r'\b', '', text_lower, flags=re.IGNORECASE)
    
    text_lower = re.sub(r'\s+', ' ', text_lower).strip()
    
    text_lower = re.sub(r'[^\w@.\s-]', '', text_lower)
    
    if '@' not in text_lower:
        text_lower = re.sub(r'([a-z0-9])\s*,\s*([a-z0-9])', r'\1\2', text_lower, flags=re.IGNORECASE)
    else:
        parts_before_at = text_lower.split('@')
        if len(parts_before_at) >= 1:
            local_part_raw = parts_before_at[0]
            local_part_cleaned = re.sub(r'([a-z0-9])\s*,\s*([a-z0-9])', r'\1\2', local_part_raw, flags=re.IGNORECASE)
            text_lower = local_part_cleaned + '@' + '@'.join(parts_before_at[1:])
    
    if '@' in text_lower:
        parts = text_lower.split('@')
        if len(parts) == 2:
            local_part = parts[0].strip()
            
            local_part = re.sub(r'[.,?;:!]+$', '', local_part)
            
            local_part = re.sub(r'\s*,\s*', ' ', local_part)
            local_part = re.sub(r'\s+', '', local_part)
            local_part = re.sub(r'[^\w._+-]', '', local_part)
            
            if not local_part:
                return None
            
            domain_part = parts[1].strip()
            domain_part = re.sub(r'[.,?;:!]+$', '', domain_part)
            domain_lower = domain_part.lower()
            
            has_dot = '.' in domain_part
            
            if not has_dot and 'dot' in domain_lower:
                domain_part = re.sub(r'\bdot\b', '.', domain_part, flags=re.IGNORECASE)
                has_dot = '.' in domain_part
            
            if has_dot:
                domain_parts = domain_part.split('.')
                domain_parts = [re.sub(r'\s+', '', part.strip()).lower() for part in domain_parts if part.strip()]
                domain_part = '.'.join(domain_parts)
                domain_part = re.sub(r'\.{2,}', '.', domain_part)
                domain_part = domain_part.strip('.')
            else:
                domain_part = re.sub(r'\s+', '', domain_part).lower()
            
            domain_part = re.sub(r'[^\w.-]', '', domain_part)
            
            if '.' in domain_part:
                domain_part = re.sub(r'\.com\.com+$', '.com', domain_part, flags=re.IGNORECASE)
                domain_part = re.sub(r'\.net\.net+$', '.net', domain_part, flags=re.IGNORECASE)
                domain_part = re.sub(r'\.org\.org+$', '.org', domain_part, flags=re.IGNORECASE)
                domain_part = re.sub(r'\.com\.com', '.com', domain_part, flags=re.IGNORECASE)
                domain_part = re.sub(r'gmailcom\.com$', 'gmail.com', domain_part, flags=re.IGNORECASE)
                domain_part = re.sub(r'yahooom\.com$', 'yahoo.com', domain_part, flags=re.IGNORECASE)
                domain_part = re.sub(r'hotmailcom\.com$', 'hotmail.com', domain_part, flags=re.IGNORECASE)
                domain_part = re.sub(r'outlookom\.com$', 'outlook.com', domain_part, flags=re.IGNORECASE)
                domain_part = domain_part.lower()
            else:
                if 'gmail' in domain_part or (len(domain_part) >= 2 and domain_part[:2] == 'gm'):
                    domain_part = 'gmail.com'
                elif 'yahoo' in domain_part:
                    domain_part = 'yahoo.com'
                elif 'hotmail' in domain_part:
                    domain_part = 'hotmail.com'
                elif 'outlook' in domain_part:
                    domain_part = 'outlook.com'
                elif domain_part and domain_part.isalpha() and len(domain_part) >= 2:
                    domain_part = domain_part + '.com'
            
            if local_part and domain_part:
                text_lower = local_part + '@' + domain_part
    else:
        text_lower = re.sub(r'[^\w@.]', '', text_lower)
    
    text_lower = re.sub(r'\.{2,}', '.', text_lower)
    text_lower = text_lower.strip('.')
    
    if '@' in text_lower:
        parts = text_lower.split('@')
        if len(parts) == 2:
            local = parts[0].strip('._+-')
            domain = parts[1].strip('._-')
            
            if domain:
                domain = re.sub(r'^gmailcom\.com$', 'gmail.com', domain, flags=re.IGNORECASE)
                domain = re.sub(r'^yahooom\.com$', 'yahoo.com', domain, flags=re.IGNORECASE)
                domain = re.sub(r'^hotmailcom\.com$', 'hotmail.com', domain, flags=re.IGNORECASE)
                domain = re.sub(r'^outlookom\.com$', 'outlook.com', domain, flags=re.IGNORECASE)
                
                domain = re.sub(r'\.com\.com+$', '.com', domain, flags=re.IGNORECASE)
                domain = re.sub(r'\.net\.net+$', '.net', domain, flags=re.IGNORECASE)
                domain = re.sub(r'\.org\.org+$', '.org', domain, flags=re.IGNORECASE)
                
                if '.' not in domain:
                    domain_lower = domain.lower()
                    if 'gmail' in domain_lower or domain_lower[:2] == 'gm':
                        domain = 'gmail.com'
                    elif 'yahoo' in domain_lower:
                        domain = 'yahoo.com'
                    elif 'hotmail' in domain_lower:
                        domain = 'hotmail.com'
                    elif 'outlook' in domain_lower:
                        domain = 'outlook.com'
                    elif domain and domain.isalpha() and len(domain) >= 2:
                        domain = domain + '.com'
            
            if local and domain:
                text_lower = local + '@' + domain
    
    if validate_email(text_lower):
        return text_lower
    
    return None

def validate_email(email: str) -> bool:
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def extract_phone_number(text: str) -> Optional[str]:
    if not text:
        return None
    
    text_lower = text.lower()
    text_lower = re.sub(r'\b(phone|number|is|my|the|a|an|yeah|yes)\b', '', text_lower)
    
    text_lower = re.sub(r'\b(triple|three times)\b', ' 333 ', text_lower)
    text_lower = re.sub(r'\b(double|two times)\b', '', text_lower)
    
    has_plus = '+' in text_lower or 'plus' in text_lower
    
    number_words = {
        'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
        'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9'
    }
    for word, digit in number_words.items():
        text_lower = re.sub(r'\b' + word + r'\b', digit, text_lower)
    
    digits = re.findall(r'\d+', text_lower)
    if not digits:
        return None
    
    phone_digits = ''.join(digits)
    
    if phone_digits.startswith('0'):
        if len(phone_digits) >= 10:
            phone_digits = '+92' + phone_digits[1:]
        else:
            return None
    elif phone_digits.startswith('92'):
        phone_digits = '+' + phone_digits
    elif has_plus or len(phone_digits) >= 10:
        if not phone_digits.startswith('+'):
            if len(phone_digits) == 10:
                phone_digits = '+92' + phone_digits
            elif len(phone_digits) == 11 and phone_digits[0] == '0':
                phone_digits = '+92' + phone_digits[1:]
            elif len(phone_digits) >= 12:
                phone_digits = '+' + phone_digits
            else:
                return None
    else:
        return None
    
    return phone_digits

def validate_phone(phone: str) -> bool:
    if not phone:
        return False
    
    normalized = extract_phone_number(phone)
    if not normalized:
        return False
    
    cleaned = normalized.replace('+', '')
    
    if len(cleaned) < 7 or len(cleaned) > 15:
        return False
    
    if not cleaned.isdigit():
        return False
    
    return True

def normalize_phone(phone: str) -> str:
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    if cleaned and cleaned[0].isdigit() and not cleaned.startswith('+'):
        cleaned = '+' + cleaned
    return cleaned

def validate_date(date_str: str) -> Optional[datetime]:
    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%B %d, %Y",
        "%b %d, %Y",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None

def validate_practice_area(text: str) -> Optional[str]:
    text_lower = text.lower().strip()
    
    text_lower = text_lower.replace("uh", "").replace("um", "").replace("okay", "").replace("ok", "")
    text_lower = " ".join(text_lower.split())
    
    if "lemon" in text_lower:
        return "Lemon Law"
    
    if "personal" in text_lower:
        if "injury" in text_lower or "injured" in text_lower or "injuries" in text_lower:
            return "Personal Injury"
        if len(text_lower.split()) <= 3:
            return "Personal Injury"
    
    if "injury" in text_lower or "injured" in text_lower or "injuries" in text_lower:
        if "personal" in text_lower or "accident" in text_lower or "car" in text_lower:
            return "Personal Injury"
    
    return None

def sanitize_input(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'[<>"\']', '', text)
    return text.strip()

