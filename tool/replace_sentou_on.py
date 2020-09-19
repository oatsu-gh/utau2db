#!/usr/bin/env python3
# coding: utf-8
# Copyright (c) oatsu
"""
先頭音の原音設定をすべて削除したのち、追加する。
"""

import utaupy as up
from os.path import splitext
from tqdm import tqdm


def delete_sentouon(otoini):
    """
    OtoIniオブジェクトから先頭音を削除したものを返す
    """
    l = []
    for oto in tqdm(otoini.values):
        if not oto.alias.startswith('- '):
            l.append(oto)
        # else:
        #     print(oto.alias)

    return up.otoini.OtoIni(l)


def pick_sentouon(otoini):
    """
    OtoIniオブジェクトから先頭音のみを取り出す
    """
    l = []
    for oto in tqdm(otoini.values):
        if oto.alias.startswith('- '):
            oto.alias = oto.alias + 'A3'
            l.append(oto)
            # print('\t', oto.alias)

    return up.otoini.OtoIni(l)


def join_otoini(otoini_no_sentouon, otoini_sentouon):
    """
    OtoIniを結合する
    先頭音がないOtoIni
    先頭音のみのOtoIni
    """
    l = otoini_no_sentouon.values + otoini_sentouon.values
    return up.otoini.OtoIni(l)


def main():
    """
    対象ファイル選択とか
    """
    path_otoini_moresampler = input('moresamplerで生成したotoiniのPATH\n>>> ').strip('"')
    path_otoini_original = input('もとのUTAU音源のotoiniのPATH\n>>> ').strip('"')
    otoini_moresampler = up.otoini.load(path_otoini_moresampler)
    otoini_original = up.otoini.load(path_otoini_original)
    otoini_moresampler = delete_sentouon(otoini_moresampler)
    otoini_original = pick_sentouon(otoini_original)
    otoini_result = join_otoini(otoini_moresampler, otoini_original)
    otoini_result.write(path_otoini_moresampler)


if __name__ == '__main__':
    main()
    input('Press Enter to exit.')
