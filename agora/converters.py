_DIGITS = '0123456789abcdefghijklmnopqrstuvwxyz'


class Base36Converter:
    regex = '[0-9a-zA-Z]+'

    def to_python(self, value):
        return int(value, 36)

    def to_url(self, value):
        n = int(value)
        if n == 0:
            return '0'
        digits = []
        while n:
            n, r = divmod(n, 36)
            digits.append(_DIGITS[r])
        return ''.join(reversed(digits))
