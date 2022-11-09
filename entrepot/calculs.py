import math


# Calcul de la densite a 15 degree
def densite15(x, y):
    # x: Temperature
    # y: Densite a la temp ambiante
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
        l = round((k / 1000), 4)
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
            l = round((k / 1000), 4)
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
                l = round((k / 1000), 4)
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
                    l = round((k / 1000), 4)
                    return l


# Calcul du VCF (Facteur de correction)
def vcf(x, y):
    # x: Densite a 15
    # y: Temperature ambiante

    y = float(y)

    if x > 1:
        x = x
    else:
        if x < 1:
            x = x * 1000

    if x >= float(839):
        a = 186.9696
        b = 0.4862
        delta = y - 15
        alpha = (a / x) / x + (b / x)
        vcfValue = math.exp((-(alpha)) * delta) - 0.8 * ((alpha) * (alpha)) * ((delta * delta))
        return round(vcfValue,5)
    else:
        if (x >= float(788)) & (x < float(839)):
            a = 594.5418
            delta = y - 15
            alpha = (a / x) / x
            vcfValue = math.exp((-(alpha) * delta) - 0.8 * ((alpha) * (alpha)) * (delta * delta))
            return round(vcfValue,5)
        else:
            if (x > float(770)) & (x < float(788)):
                a = 0.00336312
                b = 2680.3206
                delta = y - 15
                alpha = ((-a) + (b)) / x / x
                vcfValue = math.exp((-(alpha) * delta) - 0.8 * ((alpha) * (alpha)) * (delta * delta))
                return round(vcfValue,5)
            else:
                a = 346.4228
                b = 0.4388
                delta = y - 15
                alpha = (((a) / (x)) / (x)) + (b / x)
                vcfValue = math.exp((-(alpha) * delta) - 0.8 * ((alpha) * (alpha)) * (delta * delta))
                return round(vcfValue,5)


# Calcul du GSV
def gsv(x, y):
    # x: Valeur de VCF
    # y: Valeur de GOV
    y = float(y)
    gsvValue = round((x * y), 3)
    return gsvValue


# Calcul du MTV
def mtv(x, y):
    # x: Value GSV
    # y: Valeur densite a 15
    if y > 1:
        y = y
    else:
        if y < 1:
            y = y * 1000
    mtvValue = x * y / 1000
    return round(mtvValue, 3)


# Calcul du MTA
def mta(x, y):
    # x: Valeur GSV
    # y: Valeur Densite
    if y > 1:
        y = y
    else:
        if y < 1:
            y = y * 1000
    mtaValue = ((y) - 1.1) * (x / 1000)
    return round(mtaValue, 3)
