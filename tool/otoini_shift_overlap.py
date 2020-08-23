#!python
# coding: utf-8
# Copyright (c) oatsu
"""
オーバーラップをずらす（子音長を変更する）
"""

from glob import glob
from pprint import pprint

import utaupy as up

# 子音長の倍率
CONSONANT_DURATION_RATIO = 1/2


def main():
    """
    パスを入力させて処理する
    """
    path_otoini_dir = input('書き換えたい oto.ini があるフォルダのパスを入力してください\n>>> ')

    list_path_otoini = glob(f'{path_otoini_dir}/**/oto.ini', recursive=True)
    pprint(list_path_otoini)
    for path_otoini in list_path_otoini:
        up.backup.backup_io(path_otoini, 'in')
        otoini = up.otoini.load(path_otoini)
        for oto in otoini.values:
            oto.overlap += (oto.preutterance - oto.overlap) * (1 - CONSONANT_DURATION_RATIO)
        otoini.write(path_otoini)


if __name__ == '__main__':
    main()
