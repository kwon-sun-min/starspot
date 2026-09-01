"""밝은 별 카탈로그 + 지평좌표 투영.

상세 화면 "밤하늘" 위젯용. 육안으로 보이는 밝은 별(약 mag 3.0 이하) 중심의 카탈로그를
담고, astronomy-engine 으로 주어진 시각·지점의 지평좌표(고도/방위)로 변환한다.

좌표계: RA(적경, 시간 단위 h), Dec(적위, 도), mag(겉보기 등급). J2000 기준.
별은 사실상 고정 천체이므로 세차/고유운동은 위젯 목적상 무시한다(수 arcmin 오차).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

import astronomy as ast

KST = ZoneInfo("Asia/Seoul")
_UTC = ZoneInfo("UTC")


@dataclass(frozen=True)
class Star:
    name: str
    ra_hours: float  # 적경 (시간, 0~24)
    dec_deg: float   # 적위 (도, -90~90)
    mag: float       # 겉보기 등급


@dataclass(frozen=True)
class ProjectedStar:
    name: str
    alt: float  # 고도(도), 0 이상이면 지평선 위
    az: float   # 방위(도, 북=0 동=90)
    mag: float


# 북반구(한국)에서 보이는 밝은 별 중심의 카탈로그 (약 mag 3.2 이하).
# (이름, RA[h], Dec[deg], mag)
CATALOG: list[Star] = [
    Star("Sirius", 6.7525, -16.7161, -1.46),
    Star("Canopus", 6.3992, -52.6957, -0.74),
    Star("Arcturus", 14.2610, 19.1825, -0.05),
    Star("Vega", 18.6156, 38.7837, 0.03),
    Star("Capella", 5.2782, 45.9980, 0.08),
    Star("Rigel", 5.2423, -8.2016, 0.13),
    Star("Procyon", 7.6550, 5.2250, 0.34),
    Star("Betelgeuse", 5.9195, 7.4071, 0.50),
    Star("Achernar", 1.6286, -57.2367, 0.46),
    Star("Altair", 19.8464, 8.8683, 0.76),
    Star("Aldebaran", 4.5987, 16.5093, 0.85),
    Star("Antares", 16.4901, -26.4320, 1.09),
    Star("Spica", 13.4199, -11.1613, 0.97),
    Star("Pollux", 7.7553, 28.0262, 1.14),
    Star("Fomalhaut", 22.9608, -29.6222, 1.16),
    Star("Deneb", 20.6905, 45.2803, 1.25),
    Star("Regulus", 10.1395, 11.9672, 1.35),
    Star("Castor", 7.5767, 31.8883, 1.58),
    Star("Bellatrix", 5.4189, 6.3497, 1.64),
    Star("Elnath", 5.4382, 28.6074, 1.65),
    Star("Alnilam", 5.6036, -1.2019, 1.69),
    Star("Alnitak", 5.6793, -1.9426, 1.77),
    Star("Alioth", 12.9004, 55.9598, 1.77),
    Star("Dubhe", 11.0621, 61.7510, 1.79),
    Star("Mirfak", 3.4054, 49.8612, 1.79),
    Star("Wezen", 7.1399, -26.3932, 1.83),
    Star("Alkaid", 13.7923, 49.3133, 1.86),
    Star("Menkalinan", 5.9922, 44.9474, 1.90),
    Star("Alhena", 6.6285, 16.3993, 1.92),
    Star("Mintaka", 5.5334, -0.2991, 2.23),
    Star("Polaris", 2.5303, 89.2641, 1.98),
    Star("Alphard", 9.4597, -8.6586, 1.98),
    Star("Hamal", 2.1195, 23.4624, 2.00),
    Star("Diphda", 0.7265, -17.9866, 2.04),
    Star("Nunki", 18.9211, -26.2967, 2.05),
    Star("Menkent", 14.1114, -36.3700, 2.06),
    Star("Alpheratz", 0.1398, 29.0904, 2.06),
    Star("Mirach", 1.1622, 35.6206, 2.05),
    Star("Kochab", 14.8451, 74.1555, 2.08),
    Star("Rasalhague", 17.5822, 12.5600, 2.08),
    Star("Denebola", 11.8177, 14.5720, 2.14),
    Star("Algol", 3.1361, 40.9556, 2.12),
    Star("Almach", 2.0650, 42.3297, 2.10),
    Star("Tiaki", 22.7113, -46.8846, 2.07),
    Star("Muhlifain", 12.6919, -48.9599, 2.20),
    Star("Aspidiske", 9.2847, -59.2753, 2.21),
    Star("Alnair", 22.1372, -46.9610, 1.74),
    Star("Mizar", 13.3988, 54.9254, 2.23),
    Star("Sadr", 20.3705, 40.2567, 2.23),
    Star("Schedar", 0.6751, 56.5373, 2.24),
    Star("Eltanin", 17.9434, 51.4889, 2.24),
    Star("Caph", 0.1530, 59.1498, 2.28),
    Star("Naos", 8.0597, -40.0031, 2.21),
    Star("Dschubba", 16.0056, -22.6217, 2.29),
    Star("Larawag", 17.5601, -37.1038, 2.29),
    Star("Merak", 11.0307, 56.3824, 2.37),
    Star("Izar", 14.7498, 27.0742, 2.37),
    Star("Enif", 21.7364, 9.8750, 2.38),
    Star("Ankaa", 0.4381, -42.3061, 2.40),
    Star("Phecda", 11.8972, 53.6948, 2.44),
    Star("Sabik", 17.1729, -15.7249, 2.43),
    Star("Scheat", 23.0629, 28.0828, 2.44),
    Star("Alderamin", 21.3097, 62.5856, 2.45),
    Star("Markab", 23.0793, 15.2053, 2.49),
    Star("Aljanah", 20.7701, 33.9703, 2.48),
    Star("Acrab", 16.0906, -19.8054, 2.56),
    Star("Zosma", 11.2351, 20.5237, 2.56),
    Star("Arneb", 5.5455, -17.8223, 2.58),
    Star("Ascella", 19.0435, -29.8801, 2.60),
    Star("Bat Kaitos", 1.7346, -15.9375, 2.63),
    Star("Unukalhai", 15.7378, 6.4256, 2.63),
    Star("Sheratan", 1.9107, 20.8080, 2.64),
    Star("Kaus Media", 18.3499, -29.8281, 2.70),
    Star("Rasalgethi", 17.2443, 14.3903, 2.78),
    Star("Nihal", 5.4707, -20.7594, 2.81),
    Star("Algieba", 10.3328, 19.8415, 2.28),
    Star("Mirzam", 6.3783, -17.9559, 1.98),
    Star("Adhara", 6.9770, -28.9721, 1.50),
    Star("Saiph", 5.7959, -9.6696, 2.09),
    Star("Gacrux", 12.5194, -57.1132, 1.63),
    Star("Shaula", 17.5602, -37.1038, 1.62),
    Star("Kaus Australis", 18.4029, -34.3846, 1.85),
    Star("Avior", 8.3752, -59.5095, 1.86),
    Star("Atria", 16.8110, -69.0277, 1.91),
    Star("Alsephina", 8.7455, -54.7086, 1.75),
    Star("Peacock", 20.4275, -56.7351, 1.94),
]


@dataclass(frozen=True)
class ConstellationDef:
    """별자리 정의: 이름 + 구성 별(RA/Dec) + 연결선(별 인덱스 쌍)."""

    name_ko: str
    name: str
    star_coords: list[tuple[float, float]]  # (ra_hours, dec_deg)
    lines: list[tuple[int, int]]            # star_coords 인덱스 쌍


# 계절 대표 별자리 12개 (한국에서 알아보기 쉬운 것 위주).
# 각 별자리의 주요 별 좌표(RA h, Dec deg, J2000)와 연결선.
CONSTELLATIONS: list[ConstellationDef] = [
    ConstellationDef(
        "오리온자리", "Orion",
        [
            (5.9195, 7.4071),   # 0 Betelgeuse
            (5.4189, 6.3497),   # 1 Bellatrix
            (5.6036, -1.2019),  # 2 Alnilam (belt mid)
            (5.5334, -0.2991),  # 3 Mintaka (belt)
            (5.6793, -1.9426),  # 4 Alnitak (belt)
            (5.2423, -8.2016),  # 5 Rigel
            (5.7959, -9.6696),  # 6 Saiph
        ],
        [(0, 1), (1, 3), (3, 2), (2, 4), (4, 0), (3, 5), (4, 6), (5, 6)],
    ),
    ConstellationDef(
        "큰곰자리(북두칠성)", "Ursa Major",
        [
            (11.0621, 61.7510),  # 0 Dubhe
            (11.0307, 56.3824),  # 1 Merak
            (11.8972, 53.6948),  # 2 Phecda
            (12.2574, 57.0326),  # 3 Megrez
            (12.9004, 55.9598),  # 4 Alioth
            (13.3988, 54.9254),  # 5 Mizar
            (13.7923, 49.3133),  # 6 Alkaid
        ],
        [(0, 1), (1, 2), (2, 3), (3, 0), (3, 4), (4, 5), (5, 6)],
    ),
    ConstellationDef(
        "카시오페이아자리", "Cassiopeia",
        [
            (0.1530, 59.1498),   # 0 Caph
            (0.6751, 56.5373),   # 1 Schedar
            (0.9451, 60.7167),   # 2 Gamma Cas
            (1.4303, 60.2353),   # 3 Ruchbah
            (1.9066, 63.6701),   # 4 Segin
        ],
        [(0, 1), (1, 2), (2, 3), (3, 4)],
    ),
    ConstellationDef(
        "백조자리", "Cygnus",
        [
            (20.6905, 45.2803),  # 0 Deneb
            (20.3705, 40.2567),  # 1 Sadr
            (19.4948, 27.9597),  # 2 Albireo
            (19.7495, 45.1308),  # 3 Delta Cyg
            (20.7701, 33.9703),  # 4 Gienah (Aljanah)
        ],
        [(0, 1), (1, 2), (1, 3), (1, 4)],
    ),
    ConstellationDef(
        "거문고자리", "Lyra",
        [
            (18.6156, 38.7837),  # 0 Vega
            (18.7466, 37.6051),  # 1 Sheliak
            (18.9822, 32.6896),  # 2 Sulafat
            (18.9089, 36.8986),  # 3 Delta Lyr
        ],
        [(0, 1), (1, 2), (2, 3), (3, 0)],
    ),
    ConstellationDef(
        "독수리자리", "Aquila",
        [
            (19.8464, 8.8683),   # 0 Altair
            (19.7710, 10.6133),  # 1 Tarazed
            (19.9218, 6.4068),   # 2 Alshain
            (19.4260, 3.1148),   # 3 Delta Aql
        ],
        [(1, 0), (0, 2), (0, 3)],
    ),
    ConstellationDef(
        "전갈자리", "Scorpius",
        [
            (16.4901, -26.4320),  # 0 Antares
            (16.0056, -22.6217),  # 1 Dschubba
            (15.9829, -26.1140),  # 2 Pi Sco
            (17.5602, -37.1038),  # 3 Shaula
            (17.7082, -39.0299),  # 4 Lesath
            (16.8360, -38.0473),  # 5 Sargas
        ],
        [(1, 0), (2, 0), (0, 5), (5, 3), (3, 4)],
    ),
    ConstellationDef(
        "사자자리", "Leo",
        [
            (10.1395, 11.9672),  # 0 Regulus
            (10.3328, 19.8415),  # 1 Algieba
            (10.2787, 23.4173),  # 2 Adhafera
            (9.7644, 23.7740),   # 3 Rasalas
            (11.2351, 20.5237),  # 4 Zosma
            (11.8177, 14.5720),  # 5 Denebola
        ],
        [(0, 1), (1, 2), (2, 3), (1, 4), (4, 5)],
    ),
    ConstellationDef(
        "쌍둥이자리", "Gemini",
        [
            (7.5767, 31.8883),   # 0 Castor
            (7.7553, 28.0262),   # 1 Pollux
            (6.6285, 16.3993),   # 2 Alhena
            (6.7327, 25.1311),   # 3 Mebsuta
        ],
        [(0, 1), (0, 3), (3, 2)],
    ),
    ConstellationDef(
        "페가수스자리", "Pegasus",
        [
            (0.1398, 29.0904),   # 0 Alpheratz
            (23.0793, 15.2053),  # 1 Markab
            (23.0629, 28.0828),  # 2 Scheat
            (0.2206, 15.1836),   # 3 Algenib
        ],
        [(0, 2), (2, 1), (1, 3), (3, 0)],
    ),
    ConstellationDef(
        "안드로메다자리", "Andromeda",
        [
            (0.1398, 29.0904),   # 0 Alpheratz
            (1.1622, 35.6206),   # 1 Mirach
            (2.0650, 42.3297),   # 2 Almach
        ],
        [(0, 1), (1, 2)],
    ),
    ConstellationDef(
        "황소자리", "Taurus",
        [
            (4.5987, 16.5093),   # 0 Aldebaran
            (5.4382, 28.6074),   # 1 Elnath
            (4.4767, 15.9622),   # 2 Prima Hyadum
            (3.7914, 24.1051),   # 3 Alcyone (Pleiades 근처)
        ],
        [(2, 0), (0, 1), (2, 3)],
    ),
]


def _to_time(dt: datetime) -> ast.Time:
    if dt.tzinfo is None:
        raise ValueError("naive datetime 은 허용하지 않습니다.")
    u = dt.astimezone(_UTC)
    return ast.Time.Make(u.year, u.month, u.day, u.hour, u.minute, u.second + u.microsecond / 1e6)


@dataclass(frozen=True)
class ProjectedConstellation:
    name: str
    name_ko: str
    points: list[tuple[float, float]]  # 각 별의 (alt, az)
    lines: list[tuple[int, int]]


def project_constellations(
    lat: float, lon: float, when: datetime, min_above_ratio: float = 0.6
) -> list[ProjectedConstellation]:
    """지평선 위에 대부분(min_above_ratio 이상) 떠 있는 별자리만 투영해 반환한다.

    별자리의 모든 별을 alt/az 로 변환하되, 지평선 아래 별이 많으면(관측 불가) 제외한다.
    선(lines)은 원 인덱스를 유지하므로, 프론트에서 alt<0 인 끝점은 그리지 않으면 된다.
    """
    obs = ast.Observer(lat, lon, 0.0)
    t = _to_time(when)
    out: list[ProjectedConstellation] = []
    for c in CONSTELLATIONS:
        pts: list[tuple[float, float]] = []
        above = 0
        for ra_h, dec in c.star_coords:
            hor = ast.Horizon(t, obs, ra_h, dec, ast.Refraction.Normal)
            pts.append((hor.altitude, hor.azimuth))
            if hor.altitude > 0.0:
                above += 1
        if above / len(c.star_coords) >= min_above_ratio:
            out.append(
                ProjectedConstellation(name=c.name, name_ko=c.name_ko, points=pts, lines=c.lines)
            )
    return out


def project_sky(
    lat: float, lon: float, when: datetime, mag_limit: float = 3.2
) -> list[ProjectedStar]:
    """주어진 시각·지점에서 지평선 위에 있는 밝은 별들의 (alt, az) 목록을 반환한다."""
    if when.tzinfo is None:
        raise ValueError("naive datetime 은 허용하지 않습니다.")
    obs = ast.Observer(lat, lon, 0.0)
    t = _to_time(when)
    out: list[ProjectedStar] = []
    for s in CATALOG:
        if s.mag > mag_limit:
            continue
        hor = ast.Horizon(t, obs, s.ra_hours, s.dec_deg, ast.Refraction.Normal)
        if hor.altitude <= 0.0:
            continue  # 지평선 아래는 제외
        out.append(ProjectedStar(name=s.name, alt=hor.altitude, az=hor.azimuth, mag=s.mag))
    return out
