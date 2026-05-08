new = r"""
@article{bantie_et_al_2025,
  title={Physical and mechanical properties of highland bamboo (Oldeania alpina) landraces and culm sections},
  author={Bantie, Z. and Tegegne, A. G. and Gebremariam, Y.},
  journal={Advances in Bamboo Science},
  volume={12},
  pages={100172},
  year={2025},
  doi={10.1016/j.bamboo.2025.100172}
}

@article{bhat_2003,
  title={Anatomical changes during culm maturation in Bambusa bambos (L.) Voss and Dendrocalamus strictus Nees},
  author={Bhat, K. M.},
  journal={Journal of Bamboo and Rattan},
  volume={2},
  number={2},
  pages={153--166},
  year={2003},
  doi={10.1163/156915903322320766}
}

@article{hirimburegama_gamage_1995,
  title={Propagation of Bambusa vulgaris (yellow bamboo) through nodal bud culture},
  author={Hirimburegama, K. and Gamage, N.},
  journal={Journal of Horticultural Science},
  volume={70},
  number={3},
  pages={469--475},
  year={1995},
  doi={10.1080/14620316.1995.11515317}
}

@article{hossain_et_al_2005,
  title={Effect of light intensity and rooting hormone on propagation of Bambusa vulgaris Schrad ex Wendl. by branch cutting},
  author={Hossain, M. K. and Islam, S. A. and Hossain, M. A.},
  journal={Journal of Bamboo and Rattan},
  volume={4},
  number={3},
  pages={231--241},
  year={2005},
  doi={10.1163/156915905774310025}
}

@article{kalanzi_mwanja_2023,
  title={Effect of nodal cutting position and plant growth regulator on bud sprouting of Dendrocalamus giganteus Wall. Ex Munro in Uganda},
  author={Kalanzi, F. and Mwanja, C. K.},
  journal={Advances in Bamboo Science},
  volume={2},
  pages={100016},
  year={2023},
  doi={10.1016/j.bamboo.2023.100016}
}

@article{khatun_et_al_2025,
  title={Preservative treatment of the bamboos Dendrocalamus giganteus, Bambusa vulgaris and Gigantochloa nigrociliata},
  author={Khatun, R. and Ahmmed, E. and Ferdousi, S. and Khan, M. A. R. and Hannan, M. O. and Ashaduzzaman, M. and Sikder, A. and Das, A. K.},
  journal={Advances in Bamboo Science},
  volume={11},
  pages={100163},
  year={2025},
  doi={10.1016/j.bamboo.2025.100163}
}

@article{hafhouf_abbeche_2023,
  title={Impact of drying-wetting cycles on shear properties, suction, and collapse of sebkha soils},
  author={Hafhouf, I. and Abbeche, K.},
  journal={Heliyon},
  volume={9},
  number={2},
  pages={e13594},
  year={2023},
  doi={10.1016/j.heliyon.2023.e13594}
}

@incollection{galia_et_al_2022,
  title={Effect of Check Dams on Sediment Connectivity},
  author={Galia, T. and Skarpich, V. and Smazak, I.},
  booktitle={Check Dam Construction for Sustainable Watershed Management and Planning},
  pages={245--252},
  year={2022},
  publisher={Wiley},
  doi={10.1002/9781119742449.ch12}
}
"""
import os
p = os.path.join(os.path.dirname(__file__), '..', '1-MANUSCRITOS', 'referencias_artigos.bib')
with open(p, 'a', encoding='utf-8') as f:
    f.write(new)
print('Appended.')
