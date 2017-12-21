
GROUPS = {
    'grp_physics': {
        'name': 'Physics',
        'start_year': 1991,
        'default_archive': 'hep-th'
    },
    'grp_math': {
        'name': 'Mathematics',
        'start_year': 1992,
        'default_archive': 'math'
    },
    'grp_q-bio': {
        'name': 'Quantitative Biology',
        'start_year': 1992,
        'default_archive': 'q-bio'
    },
    'grp_cs': {
        'name': 'Computer Science',
        'start_year': 1993,
        'default_archive': 'cs'
    },
    'grp_test': {
        'name': 'Test',
        'start_year': 1995,
        'is_test': True
    },
    'grp_q-fin': {
        'name': 'Quantitative Finance',
        'start_year': 1997
    },
    'grp_stat': {
        'name': 'Statistics',
        'start_year': 1999
    },
    'grp_eess': {
        'name': 'Electrical Engineering and Systems Science',
        'start_year': 2017
    },
    'grp_econ': {
        'name': 'Economics',
        'start_year': 2017
    }
}
DEFAULT_GROUP = 'physics'

ARCHIVES = {
    'acc-phys': {
        'name': 'Accelerator Physics',
        'in_group': 'grp_physics',
        'start_date': '1994-11',
        'end_date': '1996-09',
    },
    'adap-org': {
        'name': 'Adaptation, Noise, and Self-Organizing Systems',
        'in_group': 'grp_physics',
        'start_date': '1993-03',
        'end_date': '1999-12',
    },
    'alg-geom': {
        'name': 'Algebraic Geometry',
        'in_group': 'grp_math',
        'start_date': '1992-02',
        'end_date': '1997-12',
    },
    'ao-sci': {
        'name': 'Atmospheric-Oceanic Sciences',
        'in_group': 'grp_physics',
        'start_date': '1995-02',
        'end_date': '1996-09',
    },
    'astro-ph': {
        'name': 'Astrophysics',
        'in_group': 'grp_physics',
        'start_date': '1992-04',
    },
    'atom-ph': {
        'name': 'Atomic, Molecular and Optical Physics',
        'in_group': 'grp_physics',
        'start_date': '1995-09',
        'end_date': '1996-09',
    },
    'bayes-an': {
        'name': 'Bayesian Analysis',
        'in_group': 'grp_physics',
        'start_date': '1995-06',
        'end_date': '1996-11',
    },
    'chao-dyn': {
        'name': 'Chaotic Dynamics',
        'in_group': 'grp_physics',
        'start_date': '1993-01',
        'end_date': '1999-12',
    },
    'chem-ph': {
        'name': 'Chemical Physics',
        'in_group': 'grp_physics',
        'start_date': '1994-03',
        'end_date': '1996-09',
    },
    'cmp-lg': {
        'name': 'Computation and Language',
        'in_group': 'grp_cs',
        'start_date': '1994-04',
        'end_date': '1998-09',
    },
    'comp-gas': {
        'name': 'Cellular Automata and Lattice Gases',
        'in_group': 'grp_physics',
        'start_date': '1993-02',
        'end_date': '1999-12',
    },
    'cond-mat': {
        'name': 'Condensed Matter',
        'in_group': 'grp_physics',
        'start_date': '1992-04',
    },
    'cs': {
        'name': 'Computer Science',
        'in_group': 'grp_cs',
        'start_date': '1993-01',
    },
    'dg-ga': {
        'name': 'Differential Geometry',
        'in_group': 'grp_math',
        'start_date': '1994-06',
        'end_date': '1997-12',
    },
    'econ': {
        'name': 'Economics',
        'in_group': 'grp_econ',
        'start_date': '2017-09',
    },
    'eess': {
        'name': 'Electrical Engineering and Systems Science',
        'in_group': 'grp_eess',
        'start_date': '2017-09',
    },
    'funct-an': {
        'name': 'Functional Analysis',
        'in_group': 'grp_math',
        'start_date': '1992-04',
        'end_date': '1997-12',
    },
    'gr-qc': {
        'name': 'General Relativity and Quantum Cosmology',
        'in_group': 'grp_physics',
        'start_date': '1992-07',
    },
    'hep-ex': {
        'name': 'High Energy Physics - Experiment',
        'in_group': 'grp_physics',
        'start_date': '1994-04',
    },
    'hep-lat': {
        'name': 'High Energy Physics - Lattice',
        'in_group': 'grp_physics',
        'start_date': '1992-02',
    },
    'hep-ph': {
        'name': 'High Energy Physics - Phenomenology',
        'in_group': 'grp_physics',
        'start_date': '1992-03',
    },
    'hep-th': {
        'name': 'High Energy Physics - Theory',
        'in_group': 'grp_physics',
        'start_date': '1991-08',
    },
    'math': {
        'name': 'Mathematics',
        'in_group': 'grp_math',
        'start_date': '1992-02',
    },
    'math-ph': {
        'name': 'Mathematical Physics',
        'in_group': 'grp_physics',
        'start_date': '1996-09',
    },
    'mtrl-th': {
        'name': 'Materials Theory',
        'in_group': 'grp_physics',
        'start_date': '1994-11',
        'end_date': '1996-09',
    },
    'nlin': {
        'name': 'Nonlinear Sciences',
        'in_group': 'grp_physics',
        'start_date': '1993-01',
    },
    'nucl-ex': {
        'name': 'Nuclear Experiment',
        'in_group': 'grp_physics',
        'start_date': '1994-12',
    },
    'nucl-th': {
        'name': 'Nuclear Theory',
        'in_group': 'grp_physics',
        'start_date': '1992-10',
    },
    'patt-sol': {
        'name': 'Pattern Formation and Solitons',
        'in_group': 'grp_physics',
        'start_date': '1993-02',
        'end_date': '1999-12',
    },
    'physics': {
        'name': 'Physics',
        'in_group': 'grp_physics',
        'start_date': '1996-10',
    },
    'plasm-ph': {
        'name': 'Plasma Physics',
        'in_group': 'grp_physics',
        'start_date': '1995-09',
        'end_date': '1996-09',
    },
    'q-alg': {
        'name': 'Quantum Algebra and Topology',
        'in_group': 'grp_math',
        'start_date': '1994-12',
        'end_date': '1997-12',
    },
    'q-bio': {
        'name': 'Quantitative Biology',
        'in_group': 'grp_q-bio',
        'start_date': '2003-09',
    },
    'q-fin': {
        'name': 'Quantitative Finance',
        'in_group': 'grp_q-fin',
        'start_date': '2008-12',
    },
    'quant-ph': {
        'name': 'Quantum Physics',
        'in_group': 'grp_physics',
        'start_date': '1994-12',
    },
    'solv-int': {
        'name': 'Exactly Solvable and Integrable Systems',
        'in_group': 'grp_physics',
        'start_date': '1993-04',
        'end_date': '1999-12',
    },
    'stat': {
        'name': 'Statistics',
        'in_group': 'grp_stat',
        'start_date': '2007-04',
    },
    'supr-con': {
        'name': 'Superconductivity',
        'in_group': 'grp_physics',
        'start_date': '1994-11',
        'end_date': '1996-09',
    },
    'test': {
        'name': 'Test',
        'in_group': 'grp_test',
        'is_test': True,
        'start_date': '1995-02',
    }
}

ARCHIVES_ACTIVE = {key: value for key,
                   value in ARCHIVES.items()
                   if 'end_date' not in ARCHIVES[key]}

# defunct archives subsumed by categories
ARCHIVES_SUBSUMED = {
    'cmp-lg': 'cs.CL',
    'adap-org': 'nlin.AO',
    'comp-gas': 'nlin.CG',
    'chao-dyn': 'nlin.CD',
    'solv-int': 'nlin.SI',
    'patt-sol': 'nlin.PS',
    'alg-geom': 'math.AG',
    'dg-ga': 'math.DG',
    'funct-an': 'math.FA',
    'q-alg': 'math.QA',
    'mtrl-th': 'cond-mat.mtrl-sci',
    'supr-con': 'cond-mat.supr-con',
    'acc-phys': 'physics.acc-ph',
    'ao-sci': 'physics.ao-ph',
    'atom-ph': 'physics.atom-ph',
    'bayes-an': 'physics.data-an',
    'chem-ph': 'physics.chem-ph',
    'plasm-ph': 'physics.plasm-ph'
}

# Legacy bare-archive names used as primary and secondary
# categories for old submissions. yyyy-mm is last month allowed.
LEGACY_ARCHIVE_AS_PRIMARY = {
    'astro-ph': '2008-12',
    'cond-mat': '2004-01',
    'test': '2010-01',
}
LEGACY_ARCHIVE_AS_SECONDARY = {
    'astro-ph': '2008-12',
    'cond-mat': '2004-01',
    'q-bio': '2003-08',
    'test': '2010-01'
}

CATEGORIES = {
    'astro-ph.CO': {
        'name': 'Cosmology and Nongalactic Astrophysics',
        'in_archive': 'astro-ph',
        'description': 'Phenomenology of early universe, cosmic microwave '
                       'background, cosmological parameters, primordial '
                       'element abundances, extragalactic distance scale, '
                       'large-scale structure of the universe. Groups, '
                       'superclusters, voids, intergalactic medium. Particle '
                       'astrophysics: dark energy, dark matter, baryogenesis, '
                       'leptogenesis, inflationary models, reheating, '
                       'monopoles, WIMPs, cosmic strings, primordial black '
                       'holes, cosmological gravitational '
                       'radiation'
    },
    'astro-ph.EP': {
        'name': 'Earth and Planetary Astrophysics',
        'in_archive': 'astro-ph',
        'description': 'Interplanetary medium, planetary physics, planetary '
                       'astrobiology, extrasolar planets, comets, asteroids, '
                       'meteorites. Structure and formation of the solar '
                       'system'
    },
    'astro-ph.GA': {
        'name': 'Astrophysics of Galaxies',
        'in_archive': 'astro-ph',
        'description': 'Phenomena pertaining to galaxies or the Milky Way. '
                       'Star clusters, HII regions and planetary nebulae, the '
                       'interstellar medium, atomic and molecular clouds, '
                       'dust. Stellar populations. Galactic structure, '
                       'formation, dynamics. Galactic nuclei, bulges, disks, '
                       'halo. Active Galactic Nuclei, supermassive black '
                       'holes, quasars. Gravitational lens systems. The Milky '
                       'Way and its '
                       'contents'
    },
    'astro-ph.HE': {
        'name': 'High Energy Astrophysical Phenomena',
        'in_archive': 'astro-ph',
        'description': 'Cosmic ray production, acceleration, propagation, '
                       'detection. Gamma ray astronomy and bursts, X-rays, '
                       'charged particles, supernovae and other explosive '
                       'phenomena, stellar remnants and accretion systems, '
                       'jets, microquasars, neutron stars, pulsars, black '
                       'holes'
    },
    'astro-ph.IM': {
        'name': 'Instrumentation and Methods for Astrophysics',
        'in_archive': 'astro-ph',
        'description': 'Detector and telescope design, experiment proposals. '
                       'Laboratory Astrophysics. Methods for data analysis, '
                       'statistical methods. Software, database '
                       'design'
    },
    'astro-ph.SR': {
        'name': 'Solar and Stellar Astrophysics',
        'in_archive': 'astro-ph',
        'description': 'White dwarfs, brown dwarfs, cataclysmic variables. '
                       'Star formation and protostellar systems, stellar '
                       'astrobiology, binary and multiple systems of stars, '
                       'stellar evolution and structure, coronas. Central '
                       'stars of planetary nebulae. Helioseismology, solar '
                       'neutrinos, production and detection of gravitational '
                       'radiation from stellar '
                       'systems'
    },
    'cond-mat.dis-nn': {
        'name': 'Disordered Systems and Neural Networks',
        'in_archive': 'cond-mat',
    },
    'cond-mat.mes-hall': {
        'name': 'Mesoscale and Nanoscale Physics',
        'in_archive': 'cond-mat',
        'description': 'Semiconducting nanostructures: quantum dots, wires, '
                       'and wells. Single electronics, spintronics, 2d '
                       'electron gases, quantum Hall effect, nanotubes, '
                       'graphene, plasmonic '
                       'nanostructures'
    },
    'cond-mat.mtrl-sci': {
        'name': 'Materials Science',
        'in_archive': 'cond-mat',
        'description': 'Techniques, synthesis, characterization, structure.  '
                       'Structural phase transitions, mechanical properties, '
                       'phonons. Defects, adsorbates, '
                       'interfaces'
    },
    'cond-mat.other': {
        'name': 'Other Condensed Matter',
        'in_archive': 'cond-mat',
        'description': 'Work in condensed matter that does not fit into the '
                       'other cond-mat '
                       'classifications'
    },
    'cond-mat.quant-gas': {
        'name': 'Quantum Gases',
        'in_archive': 'cond-mat',
        'description': 'Ultracold atomic and molecular gases, Bose-Einstein '
                       'condensation, Feshbach resonances, spinor condensates,'
                       ' optical lattices, quantum simulation with cold atoms '
                       'and molecules, macroscopic interference '
                       'phenomena'
    },
    'cond-mat.soft': {
        'name': 'Soft Condensed Matter',
        'in_archive': 'cond-mat',
        'description': 'Membranes, polymers, liquid crystals, glasses, '
                       'colloids, granular '
                       'matter'
    },
    'cond-mat.stat-mech': {
        'name': 'Statistical Mechanics',
        'in_archive': 'cond-mat',
        'description': 'Phase transitions, thermodynamics, field theory, non-'
                       'equilibrium phenomena, renormalization group and '
                       'scaling, integrable models, '
                       'turbulence'
    },
    'cond-mat.str-el': {
        'name': 'Strongly Correlated Electrons',
        'in_archive': 'cond-mat',
        'description': 'Quantum magnetism, non-Fermi liquids, spin liquids, '
                       'quantum criticality, charge density waves, metal-'
                       'insulator '
                       'transitions'
    },
    'cond-mat.supr-con': {
        'name': 'Superconductivity',
        'in_archive': 'cond-mat',
        'description': 'Superconductivity: theory, models, experiment.  '
                       'Superflow in '
                       'helium'
    },
    'cs.AI': {
        'name': 'Artificial Intelligence',
        'in_archive': 'cs',
        'description': 'Covers all areas of AI except Vision, Robotics, '
                       'Machine Learning, Multiagent Systems, and Computation '
                       'and Language (Natural Language Processing), which '
                       'have separate subject areas. In particular, includes '
                       'Expert Systems, Theorem Proving (although this may '
                       'overlap with Logic in Computer Science), Knowledge '
                       'Representation, Planning, and Uncertainty in AI. '
                       'Roughly includes material in ACM Subject Classes I.2.'
                       '0, I.2.1, I.2.3, I.2.4, I.2.8, and I.2.11.'
    },
    'cs.AR': {
        'name': 'Hardware Architecture',
        'in_archive': 'cs',
        'description': 'Covers systems organization and hardware architecture.'
                       ' Roughly includes material in ACM Subject Classes C.0,'
                       ' C.1, and C.5.'
    },
    'cs.CC': {
        'name': 'Computational Complexity',
        'in_archive': 'cs',
        'description': 'Covers models of computation, complexity classes, '
                       'structural complexity, complexity tradeoffs, upper '
                       'and lower bounds. Roughly includes material in ACM '
                       'Subject Classes F.1 (computation by abstract devices),'
                       ' F.2.3 (tradeoffs among complexity measures), and F.4.'
                       '3 (formal languages), although some material in '
                       'formal languages may be more appropriate for Logic in '
                       'Computer Science. Some material in F.2.1 and F.2.2, '
                       'may also be appropriate here, but is more likely to '
                       'have Data Structures and Algorithms as the primary '
                       'subject area.'
    },
    'cs.CE': {
        'name': 'Computational Engineering, Finance, and Science',
        'in_archive': 'cs',
        'description': 'Covers applications of computer science to the '
                       'mathematical modeling of complex systems in the '
                       'fields of science, engineering, and finance. Papers '
                       'here are interdisciplinary and applications-oriented, '
                       'focusing on techniques and tools that enable '
                       'challenging computational simulations to be performed,'
                       ' for which the use of supercomputers or distributed '
                       'computing platforms is often required. Includes '
                       'material in ACM Subject Classes J.2, J.3, and J.4 ('
                       'economics).'
    },
    'cs.CG': {
        'name': 'Computational Geometry',
        'in_archive': 'cs',
        'description': 'Roughly includes material in ACM Subject Classes I.3.'
                       '5 and F.2.2.'
    },
    'cs.CL': {
        'name': 'Computation and Language',
        'in_archive': 'cs',
        'description': 'Covers natural language processing. Roughly includes '
                       'material in ACM Subject Class I.2.7. Note that work '
                       'on artificial languages (programming languages, '
                       'logics, formal systems) that does not explicitly '
                       'address natural-language issues broadly construed ('
                       'natural-language processing, computational '
                       'linguistics, speech, text retrieval, etc.) is not '
                       'appropriate for this area.'
    },
    'cs.CR': {
        'name': 'Cryptography and Security',
        'in_archive': 'cs',
        'description': 'Covers all areas of cryptography and security '
                       'including authentication, public key cryptosytems, '
                       'proof-carrying code, etc. Roughly includes material '
                       'in ACM Subject Classes D.4.6 and E.3.'
    },
    'cs.CV': {
        'name': 'Computer Vision and Pattern Recognition',
        'in_archive': 'cs',
        'description': 'Covers image processing, computer vision, pattern '
                       'recognition, and scene understanding. Roughly '
                       'includes material in ACM Subject Classes I.2.10, I.4, '
                       'and I.5.'
    },
    'cs.CY': {
        'name': 'Computers and Society',
        'in_archive': 'cs',
        'description': 'Covers impact of computers on society, computer '
                       'ethics, information technology and public policy, '
                       'legal aspects of computing, computers and education. '
                       'Roughly includes material in ACM Subject Classes K.0, '
                       'K.2, K.3, K.4, K.5, and K.7.'
    },
    'cs.DB': {
        'name': 'Databases',
        'in_archive': 'cs',
        'description': 'Covers database management, datamining, and data '
                       'processing. Roughly includes material in ACM Subject '
                       'Classes E.2, E.5, H.0, H.2, and J.1.'
    },
    'cs.DC': {
        'name': 'Distributed, Parallel, and Cluster Computing',
        'in_archive': 'cs',
        'description': 'Covers fault-tolerance, distributed algorithms, '
                       'stabilility, parallel computation, and cluster '
                       'computing. Roughly includes material in ACM Subject '
                       'Classes C.1.2, C.1.4, C.2.4, D.1.3, D.4.5, D.4.7, E.1.'
    },
    'cs.DL': {
        'name': 'Digital Libraries',
        'in_archive': 'cs',
        'description': 'Covers all aspects of the digital library design and '
                       'document and text creation. Note that there will be '
                       'some overlap with Information Retrieval (which is a '
                       'separate subject area). Roughly includes material in '
                       'ACM Subject Classes H.3.5, H.3.6, H.3.7, I.7.'
    },
    'cs.DM': {
        'name': 'Discrete Mathematics',
        'in_archive': 'cs',
        'description': 'Covers combinatorics, graph theory, applications of '
                       'probability. Roughly includes material in ACM Subject '
                       'Classes G.2 and G.3.'
    },
    'cs.DS': {
        'name': 'Data Structures and Algorithms',
        'in_archive': 'cs',
        'description': 'Covers data structures and analysis of algorithms. '
                       'Roughly includes material in ACM Subject Classes E.1, '
                       'E.2, F.2.1, and F.2.2.'
    },
    'cs.ET': {
        'name': 'Emerging Technologies',
        'in_archive': 'cs',
        'description': 'Covers approaches to information processing ('
                       'computing, communication, sensing) and bio-chemical '
                       'analysis based on alternatives to silicon CMOS-based '
                       'technologies, such as nanoscale electronic, photonic, '
                       'spin-based, superconducting, mechanical, bio-chemical '
                       'and quantum technologies (this list is not exclusive).'
                       ' Topics of interest include (1) building blocks for '
                       'emerging technologies, their scalability and adoption '
                       'in larger systems, including integration with '
                       'traditional technologies, (2) modeling, design and '
                       'optimization of novel devices and systems, (3) models '
                       'of computation, algorithm design and programming for '
                       'emerging technologies.'
    },
    'cs.FL': {
        'name': 'Formal Languages and Automata Theory',
        'in_archive': 'cs',
        'description': 'Covers automata theory, formal language theory, '
                       'grammars, and combinatorics on words. This roughly '
                       'corresponds to ACM Subject Classes F.1.1, and F.4.3. '
                       'Papers dealing with computational complexity should '
                       'go to cs.CC; papers dealing with logic should go to '
                       'cs.LO.'
    },
    'cs.GL': {
        'name': 'General Literature',
        'in_archive': 'cs',
        'description': 'Covers introductory material, survey material, '
                       'predictions of future trends, biographies, and '
                       'miscellaneous computer-science related material. '
                       'Roughly includes all of ACM Subject Class A, except '
                       'it does not include conference proceedings (which '
                       'will be listed in the appropriate subject area).'
    },
    'cs.GR': {
        'name': 'Graphics',
        'in_archive': 'cs',
        'description': 'Covers all aspects of computer graphics. Roughly '
                       'includes material in all of ACM Subject Class I.3, '
                       'except that I.3.5 is is likely to have Computational '
                       'Geometry as the primary subject area.'
    },
    'cs.GT': {
        'name': 'Computer Science and Game Theory',
        'in_archive': 'cs',
        'description': 'Covers all theoretical and applied aspects at the '
                       'intersection of computer science and game theory, '
                       'including work in mechanism design, learning in games '
                       '(which may overlap with Learning), foundations of '
                       'agent modeling in games (which may overlap with '
                       'Multiagent systems), coordination, specification and '
                       'formal methods for non-cooperative computational '
                       'environments. The area also deals with applications '
                       'of game theory to areas such as electronic commerce.'
    },
    'cs.HC': {
        'name': 'Human-Computer Interaction',
        'in_archive': 'cs',
        'description': 'Covers human factors, user interfaces, and '
                       'collaborative computing. Roughly includes material in '
                       'ACM Subject Classes H.1.2 and all of H.5, except for '
                       'H.5.1, which is more likely to have Multimedia as the '
                       'primary subject area.'
    },
    'cs.IR': {
        'name': 'Information Retrieval',
        'in_archive': 'cs',
        'description': 'Covers indexing, dictionaries, retrieval, content and '
                       'analysis. Roughly includes material in ACM Subject '
                       'Classes H.3.0, H.3.1, H.3.2, H.3.3, and H.3.4.'
    },
    'cs.IT': {
        'name': 'Information Theory',
        'in_archive': 'cs',
        'description': 'Covers theoretical and experimental aspects of '
                       'information theory and coding. Includes material in '
                       'ACM Subject Class E.4 and intersects with H.1.1.'
    },
    'cs.LG': {
        'name': 'Learning',
        'in_archive': 'cs',
        'description': 'Covers machine learning and computational (PAC) '
                       'learning. Roughly includes material in ACM Subject '
                       'Class I.2.6.'
    },
    'cs.LO': {
        'name': 'Logic in Computer Science',
        'in_archive': 'cs',
        'description': 'Covers all aspects of logic in computer science, '
                       'including finite model theory, logics of programs, '
                       'modal logic, and program verification. Programming '
                       'language semantics should have Programming Languages '
                       'as the primary subject area. Roughly includes '
                       'material in ACM Subject Classes D.2.4, F.3.1, F.4.0, '
                       'F.4.1, and F.4.2; some material in F.4.3 (formal '
                       'languages) may also be appropriate here, although '
                       'Computational Complexity is typically the more '
                       'appropriate subject area.'
    },
    'cs.MA': {
        'name': 'Multiagent Systems',
        'in_archive': 'cs',
        'description': 'Covers multiagent systems, distributed artificial '
                       'intelligence, intelligent agents, coordinated '
                       'interactions. and practical applications. Roughly '
                       'covers ACM Subject Class I.2.11.'
    },
    'cs.MM': {
        'name': 'Multimedia',
        'in_archive': 'cs',
        'description': 'Roughly includes material in ACM Subject Class H.5.1.'
    },
    'cs.MS': {
        'name': 'Mathematical Software',
        'in_archive': 'cs',
        'description': 'Roughly includes material in ACM Subject Class G.4.'
    },
    'cs.NA': {
        'name': 'Numerical Analysis',
        'in_archive': 'cs',
        'description': 'Roughly includes material in ACM Subject Class G.1.'
    },
    'cs.NE': {
        'name': 'Neural and Evolutionary Computing',
        'in_archive': 'cs',
        'description': 'Covers neural networks, connectionism, genetic '
                       'algorithms, artificial life, adaptive behavior. '
                       'Roughly includes some material in ACM Subject Class C.'
                       '1.3, I.2.6, I.5.'
    },
    'cs.NI': {
        'name': 'Networking and Internet Architecture',
        'in_archive': 'cs',
        'description': 'Covers all aspects of computer communication networks,'
                       ' including network architecture and design, network '
                       'protocols, and internetwork standards (like TCP/IP). '
                       'Also includes topics, such as web caching, that are '
                       'directly relevant to Internet architecture and '
                       'performance. Roughly includes all of ACM Subject '
                       'Class C.2 except C.2.4, which is more likely to have '
                       'Distributed, Parallel, and Cluster Computing as the '
                       'primary subject area.'
    },
    'cs.OH': {
        'name': 'Other Computer Science',
        'in_archive': 'cs',
        'description': 'This is the classification to use for documents that '
                       'do not fit anywhere else.'
    },
    'cs.OS': {
        'name': 'Operating Systems',
        'in_archive': 'cs',
        'description': 'Roughly includes material in ACM Subject Classes D.4.'
                       '1, D.4.2., D.4.3, D.4.4, D.4.5, D.4.7, and D.4.9.'
    },
    'cs.PF': {
        'name': 'Performance',
        'in_archive': 'cs',
        'description': 'Covers performance measurement and evaluation, '
                       'queueing, and simulation. Roughly includes material '
                       'in ACM Subject Classes D.4.8 and K.6.2.'
    },
    'cs.PL': {
        'name': 'Programming Languages',
        'in_archive': 'cs',
        'description': 'Covers programming language semantics, language '
                       'features, programming approaches (such as object-'
                       'oriented programming, functional programming, logic '
                       'programming). Also includes material on compilers '
                       'oriented towards programming languages; other '
                       'material on compilers may be more appropriate in '
                       'Architecture (AR). Roughly includes material in ACM '
                       'Subject Classes D.1 and D.3.'
    },
    'cs.RO': {
        'name': 'Robotics',
        'in_archive': 'cs',
        'description': 'Roughly includes material in ACM Subject Class I.2.9.'
    },
    'cs.SC': {
        'name': 'Symbolic Computation',
        'in_archive': 'cs',
        'description': 'Roughly includes material in ACM Subject Class I.1.'
    },
    'cs.SD': {
        'name': 'Sound',
        'in_archive': 'cs',
        'description': 'Covers all aspects of computing with sound, and sound '
                       'as an information channel. Includes models of sound, '
                       'analysis and synthesis, audio user interfaces, '
                       'sonification of data, computer music, and sound '
                       'signal processing. Includes ACM Subject Class H.5.5, '
                       'and intersects with H.1.2, H.5.1, H.5.2, I.2.7, I.5.4,'
                       ' I.6.3, J.5, K.4.2.'
    },
    'cs.SE': {
        'name': 'Software Engineering',
        'in_archive': 'cs',
        'description': 'Covers design tools, software metrics, testing and '
                       'debugging, programming environments, etc. Roughly '
                       'includes material in all of ACM Subject Classes D.2, '
                       'except that D.2.4 (program verification) should '
                       'probably have Logics in Computer Science as the '
                       'primary subject area.'
    },
    'cs.SI': {
        'name': 'Social and Information Networks',
        'in_archive': 'cs',
        'description': 'Covers the design, analysis, and modeling of social '
                       'and information networks, including their '
                       'applications for on-line information access, '
                       'communication, and interaction, and their roles as '
                       'datasets in the exploration of questions in these and '
                       'other domains, including connections to the social '
                       'and biological sciences. Analysis and modeling of '
                       'such networks includes topics in ACM Subject classes '
                       'F.2, G.2, G.3, H.2, and I.2; applications in '
                       'computing include topics in H.3, H.4, and H.5; and '
                       'applications at the interface of computing and other '
                       'disciplines include topics in J.1--J.7. Papers on '
                       'computer communication systems and network protocols ('
                       'e.g. TCP/IP) are generally a closer fit to the '
                       'Networking and Internet Architecture (cs.NI) category.'
    },
    'cs.SY': {
        'name': 'Systems and Control',
        'in_archive': 'cs',
        'description': 'This section includes theoretical and experimental '
                       'research covering all facets of automatic control '
                       'systems, having as focal point analysis and design '
                       'methods using tools of modeling, simulation and '
                       'optimization. Specific areas of research include '
                       'nonlinear, distributed, adaptive, stochastic and '
                       'robust control, hybrid and discrete event systems. '
                       'Application areas include automotive, aerospace, '
                       'process control, network control, biological systems, '
                       'multiagent and cooperative control, sensor networks, '
                       'control of cyberphysical and energy-related systems, '
                       'control of computing systems.'
    },
    'econ.EM': {
        'name': 'Econometrics',
        'in_archive': 'econ',
        'description': 'Econometric Theory, Micro-Econometrics, Macro-'
                       'Econometrics, Empirical Content of Economic Relations '
                       'discovered via New Methods, Methodological Aspects of '
                       'the Application of Statistical Inference to Economic '
                       'Data'
    },
    'eess.AS': {
        'name': 'Audio and Speech Processing',
        'in_archive': 'eess',
        'description': 'Theory and methods for processing signals '
                       'representing audio, speech, and language, and their '
                       'applications. This includes analysis, synthesis, '
                       'enhancement, transformation, classification and '
                       'interpretation of such signals as well as the design, '
                       'development, and evaluation of associated signal '
                       'processing systems. Machine learning and pattern '
                       'analysis applied to any of the above areas is also '
                       'welcome.  Specific topics of interest include: '
                       'auditory modeling and hearing aids; acoustic '
                       'beamforming and source localization; classification '
                       'of acoustic scenes; speaker separation; active noise '
                       'control and echo cancellation; enhancement; de-'
                       'reverberation; bioacoustics; music signals analysis, '
                       'synthesis and modification; music information '
                       'retrieval;  audio for multimedia and joint audio-'
                       'video processing; spoken and written language '
                       'modeling, segmentation, tagging, parsing, '
                       'understanding, and translation; text mining; speech '
                       'production, perception, and psychoacoustics; speech '
                       'analysis, synthesis, and perceptual modeling and '
                       'coding; robust speech recognition; speaker '
                       'recognition and characterization; deep learning, '
                       'online learning, and graphical models applied to '
                       'speech, audio, and language signals; and '
                       'implementation aspects ranging from system '
                       'architecture to fast algorithms.'
    },
    'eess.IV': {
        'name': 'Image and Video Processing',
        'in_archive': 'eess',
        'description': 'Theory, algorithms, and architectures for the '
                       'formation, capture, processing, communication, '
                       'analysis, and display of images, video, and '
                       'multidimensional signals in a wide variety of '
                       'applications. Topics of interest include: '
                       'mathematical, statistical, and perceptual image and '
                       'video modeling and representation; linear and '
                       'nonlinear filtering, de-blurring, enhancement, '
                       'restoration, and reconstruction from degraded, low-'
                       'resolution or tomographic data; lossless and lossy '
                       'compression and coding; segmentation, alignment, and '
                       'recognition; image rendering, visualization, and '
                       'printing; computational imaging, including ultrasound,'
                       ' tomographic and magnetic resonance imaging; and '
                       'image and video analysis, synthesis, storage, search '
                       'and retrieval.'
    },
    'eess.SP': {
        'name': 'Signal Processing',
        'in_archive': 'eess',
        'description': 'Theory, algorithms, performance analysis and '
                       'applications of signal and data analysis, including '
                       'physical modeling, processing, detection and '
                       'parameter estimation, learning, mining, retrieval, '
                       'and information extraction. The term "signal" '
                       'includes speech, audio, sonar, radar, geophysical, '
                       'physiological, (bio-) medical, image, video, and '
                       'multimodal natural and man-made signals, including '
                       'communication signals and data. Topics of interest '
                       'include: statistical signal processing, spectral '
                       'estimation and system identification; filter design, '
                       'adaptive filtering / stochastic learning; ('
                       'compressive) sampling, sensing, and transform-domain '
                       'methods including fast algorithms; signal processing '
                       'for machine learning and machine learning for signal '
                       'processing applications; in-network and graph signal '
                       'processing; convex and nonconvex optimization methods '
                       'for signal processing applications; radar, sonar, and '
                       'sensor array beamforming and direction finding; '
                       'communications signal processing; low power, multi-'
                       'core and system-on-chip signal processing; sensing, '
                       'communication, analysis and optimization for cyber-'
                       'physical systems such as power grids and the Internet '
                       'of Things.'
    },
    'math.AC': {
        'name': 'Commutative Algebra',
        'in_archive': 'math',
        'description': 'Commutative rings, modules, ideals, homological '
                       'algebra, computational aspects, invariant theory, '
                       'connections to algebraic geometry and '
                       'combinatorics'
    },
    'math.AG': {
        'name': 'Algebraic Geometry',
        'in_archive': 'math',
        'description': 'Algebraic varieties, stacks, sheaves, schemes, moduli '
                       'spaces, complex geometry, quantum '
                       'cohomology'
    },
    'math.AP': {
        'name': 'Analysis of PDEs',
        'in_archive': 'math',
        'description': 'Existence and uniqueness, boundary conditions, linear '
                       'and non-linear operators, stability, soliton theory, '
                       'integrable PDE\'s, conservation laws, qualitative '
                       '\'s, conservation laws, '
                       'ervation laws, '
    },
    'math.AT': {
        'name': 'Algebraic Topology',
        'in_archive': 'math',
        'description': 'Homotopy theory, homological algebra, algebraic '
                       'treatments of '
                       'manifolds'
    },
    'math.CA': {
        'name': 'Classical Analysis and ODEs',
        'in_archive': 'math',
        'description': 'Special functions, orthogonal polynomials, harmonic '
                       'analysis, ODE\'s, differential relations, calculus of '
                       '\'s, differential relations, calculus '
                       '#erential relations, calculus '
    },
    'math.CO': {
        'name': 'Combinatorics',
        'in_archive': 'math',
        'description': 'Discrete mathematics, graph theory, enumeration, '
                       'combinatorial optimization, Ramsey theory, '
                       'combinatorial game '
                       'theory'
    },
    'math.CT': {
        'name': 'Category Theory',
        'in_archive': 'math',
        'description': 'Enriched categories, topoi, abelian categories, '
                       'monoidal categories, homological '
                       'algebra'
    },
    'math.CV': {
        'name': 'Complex Variables',
        'in_archive': 'math',
        'description': 'Holomorphic functions, automorphic group actions and '
                       'forms, pseudoconvexity, complex geometry, analytic '
                       'spaces, analytic '
                       'sheaves'
    },
    'math.DG': {
        'name': 'Differential Geometry',
        'in_archive': 'math',
        'description': 'Complex, contact, Riemannian, pseudo-Riemannian and '
                       'Finsler geometry, relativity, gauge theory, global '
                       'analysis'
    },
    'math.DS': {
        'name': 'Dynamical Systems',
        'in_archive': 'math',
        'description': 'Dynamics of differential equations and flows, '
                       'mechanics, classical few-body problems, iterations, '
                       'complex dynamics, delayed differential '
                       'equations'
    },
    'math.FA': {
        'name': 'Functional Analysis',
        'in_archive': 'math',
        'description': 'Banach spaces, function spaces, real functions, '
                       'integral transforms, theory of distributions, measure '
                       'theory'
    },
    'math.GM': {
        'name': 'General Mathematics',
        'in_archive': 'math',
        'description': 'Mathematical material of general interest, topics not '
                       'covered '
                       'elsewhere'
    },
    'math.GN': {
        'name': 'General Topology',
        'in_archive': 'math',
        'description': 'Continuum theory, point-set topology, spaces with '
                       'algebraic structure, foundations, dimension theory, '
                       'local and global '
                       'properties'
    },
    'math.GR': {
        'name': 'Group Theory',
        'in_archive': 'math',
        'description': 'Finite groups, topological groups, representation '
                       'theory, cohomology, classification and '
                       'structure'
    },
    'math.GT': {
        'name': 'Geometric Topology',
        'in_archive': 'math',
        'description': 'Manifolds, orbifolds, polyhedra, cell complexes, '
                       'foliations, geometric '
                       'structures'
    },
    'math.HO': {
        'name': 'History and Overview',
        'in_archive': 'math',
        'description': 'Biographies, philosophy of mathematics, mathematics '
                       'education, recreational mathematics, communication of '
                       'mathematics'
    },
    'math.IT': {
        'name': 'Information Theory',
        'in_archive': 'math',
        'description': 'math.IT is an alias for cs.IT. Covers theoretical and '
                       'experimental aspects of information theory and coding.'
    },
    'math.KT': {
        'name': 'K-Theory and Homology',
        'in_archive': 'math',
        'description': 'Algebraic and topological K-theory, relations with '
                       'topology, commutative algebra, and operator '
                       'algebras'
    },
    'math.LO': {
        'name': 'Logic',
        'in_archive': 'math',
        'description': 'Logic, set theory, point-set topology, formal '
                       'mathematics'
    },
    'math.MG': {
        'name': 'Metric Geometry',
        'in_archive': 'math',
        'description': 'Euclidean, hyperbolic, discrete, convex, coarse '
                       'geometry, comparisons in Riemannian geometry, '
                       'symmetric '
                       'spaces'
    },
    'math.MP': {
        'name': 'Mathematical Physics',
        'in_archive': 'math',
        'description': 'Mathematical methods in quantum field theory, quantum '
                       'mechanics, statistical mechanics, condensed matter, '
                       'nuclear and atomic '
                       'physics'
    },
    'math.NA': {
        'name': 'Numerical Analysis',
        'in_archive': 'math',
        'description': 'Numerical algorithms for problems in analysis and '
                       'algebra, scientific '
                       'computation'
    },
    'math.NT': {
        'name': 'Number Theory',
        'in_archive': 'math',
        'description': 'Prime numbers, diophantine equations, analytic number '
                       'theory, algebraic number theory, arithmetic geometry, '
                       'Galois '
                       'theory'
    },
    'math.OA': {
        'name': 'Operator Algebras',
        'in_archive': 'math',
        'description': 'Algebras of operators on Hilbert space, C^*-algebras, '
                       'von Neumann algebras, non-commutative '
                       'geometry'
    },
    'math.OC': {
        'name': 'Optimization and Control',
        'in_archive': 'math',
        'description': 'Operations research, linear programming, control '
                       'theory, systems theory, optimal control, game '
                       'theory'
    },
    'math.PR': {
        'name': 'Probability',
        'in_archive': 'math',
        'description': 'Theory and applications of probability and stochastic '
                       'processes: e.g. central limit theorems, large '
                       'deviations, stochastic differential equations, models '
                       'from statistical mechanics, queuing '
                       'theory'
    },
    'math.QA': {
        'name': 'Quantum Algebra',
        'in_archive': 'math',
        'description': 'Quantum groups, skein theories, operadic and '
                       'diagrammatic algebra, quantum field '
                       'theory'
    },
    'math.RA': {
        'name': 'Rings and Algebras',
        'in_archive': 'math',
        'description': 'Non-commutative rings and algebras, non-associative '
                       'algebras, universal algebra and lattice theory, '
                       'linear algebra, '
                       'semigroups'
    },
    'math.RT': {
        'name': 'Representation Theory',
        'in_archive': 'math',
        'description': 'Linear representations of algebras and groups, Lie '
                       'theory, associative algebras, multilinear '
                       'algebra'
    },
    'math.SG': {
        'name': 'Symplectic Geometry',
        'in_archive': 'math',
        'description': 'Hamiltonian systems, symplectic flows, classical '
                       'integrable '
                       'systems'
    },
    'math.SP': {
        'name': 'Spectral Theory',
        'in_archive': 'math',
        'description': 'Schrodinger operators, operators on manifolds, '
                       'general differential operators, numerical studies, '
                       'integral operators, discrete models, resonances, non-'
                       'self-adjoint operators, random operators/'
                       'matrices'
    },
    'math.ST': {
        'name': 'Statistics Theory',
        'in_archive': 'math',
        'description': 'math.ST is an alias for stat.TH. Applied, '
                       'computational and theoretical statistics: e.g. '
                       'statistical inference, regression, time series, '
                       'multivariate analysis, data analysis, Markov chain '
                       'Monte Carlo, design of experiments, case '
                       'studies'
    },
    'nlin.AO': {
        'name': 'Adaptation and Self-Organizing Systems',
        'in_archive': 'nlin',
        'description': 'adaptation, self-organizing systems, statistical '
                       'physics, fluctuating systems, stochastic processes, '
                       'interacting particle systems, machine '
                       'learning'
    },
    'nlin.CD': {
        'name': 'Chaotic Dynamics',
        'in_archive': 'nlin',
        'description': 'dynamical systems, chaos, quantum chaos, topological '
                       'dynamics, cycle expansions, turbulence, '
                       'propagation'
    },
    'nlin.CG': {
        'name': 'Cellular Automata and Lattice Gases',
        'in_archive': 'nlin',
        'description': 'computational methods, time series analysis, signal '
                       'processing, wavelets, lattice '
                       'gases'
    },
    'nlin.PS': {
        'name': 'Pattern Formation and Solitons',
        'in_archive': 'nlin',
        'description': 'pattern formation, coherent structures, '
                       'solitons'
    },
    'nlin.SI': {
        'name': 'Exactly Solvable and Integrable Systems',
        'in_archive': 'nlin',
        'description': 'exactly solvable systems, integrable PDEs, integrable '
                       'ODEs, Painleve analysis, integrable discrete maps, '
                       'solvable lattice models, integrable quantum '
                       'systems'
    },
    'physics.acc-ph': {
        'name': 'Accelerator Physics',
        'in_archive': 'physics',
    },
    'physics.ao-ph': {
        'name': 'Atmospheric and Oceanic Physics',
        'in_archive': 'physics',
    },
    'physics.app-ph': {
        'name': 'Applied Physics',
        'in_archive': 'physics',
    },
    'physics.atm-clus': {
        'name': 'Atomic and Molecular Clusters',
        'in_archive': 'physics',
    },
    'physics.atom-ph': {
        'name': 'Atomic Physics',
        'in_archive': 'physics',
    },
    'physics.bio-ph': {
        'name': 'Biological Physics',
        'in_archive': 'physics',
    },
    'physics.chem-ph': {
        'name': 'Chemical Physics',
        'in_archive': 'physics',
    },
    'physics.class-ph': {
        'name': 'Classical Physics',
        'in_archive': 'physics',
    },
    'physics.comp-ph': {
        'name': 'Computational Physics',
        'in_archive': 'physics',
    },
    'physics.data-an': {
        'name': 'Data Analysis, Statistics and Probability',
        'in_archive': 'physics',
    },
    'physics.ed-ph': {
        'name': 'Physics Education',
        'in_archive': 'physics',
    },
    'physics.flu-dyn': {
        'name': 'Fluid Dynamics',
        'in_archive': 'physics',
    },
    'physics.gen-ph': {
        'name': 'General Physics',
        'in_archive': 'physics',
    },
    'physics.geo-ph': {
        'name': 'Geophysics',
        'in_archive': 'physics',
    },
    'physics.hist-ph': {
        'name': 'History and Philosophy of Physics',
        'in_archive': 'physics',
    },
    'physics.ins-det': {
        'name': 'Instrumentation and Detectors',
        'in_archive': 'physics',
    },
    'physics.med-ph': {
        'name': 'Medical Physics',
        'in_archive': 'physics',
    },
    'physics.optics': {
        'name': 'Optics',
        'in_archive': 'physics',
    },
    'physics.plasm-ph': {
        'name': 'Plasma Physics',
        'in_archive': 'physics',
    },
    'physics.pop-ph': {
        'name': 'Popular Physics',
        'in_archive': 'physics',
    },
    'physics.soc-ph': {
        'name': 'Physics and Society',
        'in_archive': 'physics',
    },
    'physics.space-ph': {
        'name': 'Space Physics',
        'in_archive': 'physics',
    },
    'q-bio.BM': {
        'name': 'Biomolecules',
        'in_archive': 'q-bio',
        'description': 'DNA, RNA, proteins, lipids, etc.; molecular '
                       'structures and folding kinetics; molecular '
                       'interactions; single-molecule manipulation.'
    },
    'q-bio.CB': {
        'name': 'Cell Behavior',
        'in_archive': 'q-bio',
        'description': 'Cell-cell signaling and interaction; morphogenesis '
                       'and development; apoptosis; bacterial conjugation; '
                       'viral-host interaction; '
                       'immunology'
    },
    'q-bio.GN': {
        'name': 'Genomics',
        'in_archive': 'q-bio',
        'description': 'DNA sequencing and assembly; gene and motif finding; '
                       'RNA editing and alternative splicing; genomic '
                       'structure and processes (replication, transcription, '
                       'methylation, etc); mutational processes.'
    },
    'q-bio.MN': {
        'name': 'Molecular Networks',
        'in_archive': 'q-bio',
        'description': 'Gene regulation, signal transduction, proteomics, '
                       'metabolomics, gene and enzymatic '
                       'networks'
    },
    'q-bio.NC': {
        'name': 'Neurons and Cognition',
        'in_archive': 'q-bio',
        'description': 'Synapse, cortex, neuronal dynamics, neural network, '
                       'sensorimotor control, behavior, '
                       'attention'
    },
    'q-bio.OT': {
        'name': 'Other Quantitative Biology',
        'in_archive': 'q-bio',
        'description': 'Work in quantitative biology that does not fit into '
                       'the other q-bio '
                       'classifications'
    },
    'q-bio.PE': {
        'name': 'Populations and Evolution',
        'in_archive': 'q-bio',
        'description': 'Population dynamics, spatio-temporal and '
                       'epidemiological models, dynamic speciation, co-'
                       'evolution, biodiversity, foodwebs, aging; molecular '
                       'evolution and phylogeny; directed evolution; origin '
                       'of '
                       'life'
    },
    'q-bio.QM': {
        'name': 'Quantitative Methods',
        'in_archive': 'q-bio',
        'description': 'All experimental, numerical, statistical and '
                       'mathematical contributions of value to '
                       'biology'
    },
    'q-bio.SC': {
        'name': 'Subcellular Processes',
        'in_archive': 'q-bio',
        'description': 'Assembly and control of subcellular structures ('
                       'channels, organelles, cytoskeletons, capsules, etc.); '
                       'molecular motors, transport, subcellular localization;'
                       ' mitosis and '
                       'meiosis'
    },
    'q-bio.TO': {
        'name': 'Tissues and Organs',
        'in_archive': 'q-bio',
        'description': 'Blood flow in vessels, biomechanics of bones, '
                       'electrical waves, endocrine system, tumor '
                       'growth'
    },
    'q-fin.CP': {
        'name': 'Computational Finance',
        'in_archive': 'q-fin',
        'description': 'Computational methods, including Monte Carlo, PDE, '
                       'lattice and other numerical methods with applications '
                       'to financial '
                       'modeling'
    },
    'q-fin.EC': {
        'name': 'Economics',
        'in_archive': 'q-fin',
        'description': 'Economics, including micro and macro economics, '
                       'international economics, theory of the firm, labor '
                       'economics, and other economic topics outside of '
                       'finance'
    },
    'q-fin.GN': {
        'name': 'General Finance',
        'in_archive': 'q-fin',
        'description': 'Development of general quantitative methodologies '
                       'with applications in '
                       'finance'
    },
    'q-fin.MF': {
        'name': 'Mathematical Finance',
        'in_archive': 'q-fin',
        'description': 'Mathematical and analytical methods of finance, '
                       'including stochastic, probabilistic and functional '
                       'analysis, algebraic, geometric and other '
                       'methods'
    },
    'q-fin.PM': {
        'name': 'Portfolio Management',
        'in_archive': 'q-fin',
        'description': 'Security selection and optimization, capital '
                       'allocation, investment strategies and performance '
                       'measurement'
    },
    'q-fin.PR': {
        'name': 'Pricing of Securities',
        'in_archive': 'q-fin',
        'description': 'Valuation and hedging of financial securities, their '
                       'derivatives, and structured '
                       'products'
    },
    'q-fin.RM': {
        'name': 'Risk Management',
        'in_archive': 'q-fin',
        'description': 'Measurement and management of financial risks in '
                       'trading, banking, insurance, corporate and other '
                       'applications'
    },
    'q-fin.ST': {
        'name': 'Statistical Finance',
        'in_archive': 'q-fin',
        'description': 'Statistical, econometric and econophysics analyses '
                       'with applications to financial markets and economic '
                       'data'
    },
    'q-fin.TR': {
        'name': 'Trading and Market Microstructure',
        'in_archive': 'q-fin',
        'description': 'Market microstructure, liquidity, exchange and '
                       'auction design, automated trading, agent-based '
                       'modeling and market-'
                       'making'
    },
    'stat.AP': {
        'name': 'Applications',
        'in_archive': 'stat',
        'description': 'Biology, Education, Epidemiology, Engineering, '
                       'Environmental Sciences, Medical, Physical Sciences, '
                       'Quality Control, Social '
                       'Sciences'
    },
    'stat.CO': {
        'name': 'Computation',
        'in_archive': 'stat',
        'description': 'Algorithms, Simulation, '
                       'Visualization'
    },
    'stat.ME': {
        'name': 'Methodology',
        'in_archive': 'stat',
        'description': 'Design, Surveys, Model Selection, Multiple Testing, '
                       'Multivariate Methods, Signal and Image Processing, '
                       'Time Series, Smoothing, Spatial Statistics, Survival '
                       'Analysis, Nonparametric and Semiparametric '
                       'Methods'
    },
    'stat.ML': {
        'name': 'Machine Learning',
        'in_archive': 'stat',
        'description': 'Classification, Graphical Models, High Dimensional '
                       'Inference'
    },
    'stat.OT': {
        'name': 'Other Statistics',
        'in_archive': 'stat',
        'description': 'Work in statistics that does not fit into the other '
                       'stat '
                       'classifications'
    },
    'stat.TH': {
        'name': 'Statistics Theory',
        'in_archive': 'stat',
        'description': 'Asymptotics, Bayesian Inference, Decision Theory, '
                       'Estimation, Foundations, Inference, '
                       'Testing'
    },
    'test.dis-nn': {
        'name': 'Test Disruptive Networks',
        'in_archive': 'test',
    },
    'test.mes-hall': {
        'name': 'Test Hall',
        'in_archive': 'test',
    },
    'test.mtrl-sci': {
        'name': 'Test Mtrl-Sci',
        'in_archive': 'test',
    },
    'test.soft': {
        'name': 'Test Soft',
        'in_archive': 'test',
    },
    'test.stat-mech': {
        'name': 'Test Mechanics',
        'in_archive': 'test',
    },
    'test.str-el': {
        'name': 'Test Electrons',
        'in_archive': 'test',
    },
    'test.supr-con': {
        'name': 'Test Superconductivity',
        'in_archive': 'test',
    },
}
