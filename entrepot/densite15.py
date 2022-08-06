import math


def densite15(x, y):
    t15 = x - 15
    y = float(y)
    if y > 1:
        a = y
    else:
        if y < 1:
            a = y * 1000

    if 500 <= a < 770.5:
        b = 346.4228
        c = 0.4388
        d = (1 - 0.000023 * t15) - (0.00000002 * (t15 ** 2))
        e = round(a * d, 9)
        f = round(((b / e ** 2) + (c / e)), 7)
        g = math.exp(-f * t15 * (1 + 0.8 * f * t15))
        h = e / g
        i = (b / h ** 2) + (c / h)
        j = math.exp(-i * t15 * (1 + 0.8 * i * t15))
        k = e / j
        l = round((k / 1000), 7)
        return l
    else:
        if 770.5 <= a < 786.6:
            b = 2680.3206
            c = -0.003363
            d = (1 - 0.000023 * t15) - (0.00000002 * (t15 ** 2))
            e = round(a * d, 9)
            f = round(((b / e ** 2) + (c / e)), 7)
            g = math.exp(-f * t15 * (1 + 0.8 * f * t15))
            h = e / g
            i = (b / h ** 2) + (c / h)
            j = math.exp(-i * t15 * (1 + 0.8 * i * t15))
            k = e / j
            l = round((k / 1000), 7)
            return l
        else:
            if 786.6 <= a < 839:
                b = 594.5418
                c = 0
                d = (1 - 0.000023 * t15) - (0.00000002 * (t15 ** 2))
                e = round(a * d, 9)
                f = round(((b / e ** 2) + (c / e)), 7)
                g = math.exp(-f * t15 * (1 + 0.8 * f * t15))
                h = e / g
                i = (b / h ** 2) + (c / h)
                j = math.exp(-i * t15 * (1 + 0.8 * i * t15))
                k = e / j
                l = round((k / 1000), 7)
                return l
            else:
                if a >= 839:
                    b = 186.9696
                    c = 0.4862
                    d = (1 - 0.000023 * t15) - (0.00000002 * (t15 ** 2))
                    e = round(a * d, 9)
                    f = round(((b / e ** 2) + (c / e)), 7)
                    g = math.exp(-f * t15 * (1 + 0.8 * f * t15))
                    h = e / g
                    i = (b / h ** 2) + (c / h)
                    j = math.exp(-i * t15 * (1 + 0.8 * i * t15))
                    k = e / j
                    l = round((k / 1000), 7)
                    return l
