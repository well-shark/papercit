# papercit
Generate bibliographic citations (e.g. bibtex, CJC)
> 现在仅支持**有 DOI 号**的**会议论文**和**期刊论文**。

1. 在 `article_list` 中放入需要引用的文献标题
2. 运行脚本 `python papercit.py`
3. 结果默认追加写在 `ref.bib` 文件中

示例运行结果：
```
Querying DOI for title: A Method of Few-Shot Network Intrusion Detection Based on Meta-Learning Framework
Matched DOI found for title: 10.1109/tifs.2020.2991876
Parsing bibtex:  @article{Xu_2020, t ...
RESULT: @article{Xu_2020,
	title={A Method of Few-Shot Network Intrusion Detection Based on Meta-Learning Framework},
	author={Xu, Congyuan and Shen, Jizhong and Du, Xin},
	year={2020},
	pages={3540–3552},
	publisher={Institute of Electrical and Electronics Engineers (IEEE)},
	doi={10.1109/tifs.2020.2991876},
	journal={IEEE Transactions on Information Forensics and Security},
	volume={15}
} 

Querying DOI for title: Deep fingerprinting: undermining website fingerprinting defenses with deep learning
Matched DOI found for title: 10.1145/3243734.3243768
Parsing bibtex:  @inproceedings{Siri ...
	 Warning: No matched field found for pages
Warning: Some fields are missing: ['pages', 'address']
Re-querying paper info "['pages', 'address']" for DOI: 10.1145/3243734.3243768
RESULT: @inproceedings{Sirinam_2018,
	title={Deep Fingerprinting: Undermining Website Fingerprinting Defenses with Deep Learning},
	author={Sirinam, Payap and Imani, Mohsen and Juarez, Marc and Wright, Matthew},
	year={2018},
	pages={},
	publisher={ACM},
	doi={10.1145/3243734.3243768},
	booktitle={Proceedings of the 2018 ACM SIGSAC Conference on Computer and Communications Security},
	address={Toronto Canada}
} 

Querying DOI for title: Attention is all you need
No matched DOI found for title: Attention is all you need
```

脚本会对缺失字段二次查询，但 CrossRef 数据库可能**缺页码字段**，需要手动检索补充。


TODO：
1. 需要其他文献类型可以自主修改脚本；
2. 没有 DOI 号的文献可以通过 Semantic Scholar API 查询；
3. 缺失的页码等字段也可以通过 Semantic Scholar API 补充。
