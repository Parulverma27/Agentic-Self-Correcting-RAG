import json
import os
from typing import List
from app.schemas import DocumentChunk, GoldBenchmarkItem
from app.vector_store import vector_store

# Corpus definition for HotpotQA (General Knowledge / Multi-Hop Reasoning - 30 passages)
HOTPOTQA_CORPUS = [
    DocumentChunk(
        chunk_id="hp_chunk_001",
        domain="hotpotqa",
        text="The Roman Colosseum, originally named the Flavian Amphitheatre, was commissioned by Emperor Vespasian in AD 72 and completed under his successor Titus in AD 80. Situated east of the Roman Forum, it could hold an estimated 50,000 to 80,000 spectators.",
        metadata={"title": "Colosseum Architecture", "source": "HotpotQA-History"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_002",
        domain="hotpotqa",
        text="Vespasian ruled as Roman emperor from AD 69 to AD 79. As the fourth and final ruler in the Year of the Four Emperors, he founded the Flavian dynasty that governed the Roman Empire for 27 years and reformed the imperial fiscal system.",
        metadata={"title": "Emperor Vespasian Biography", "source": "HotpotQA-History"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_003",
        domain="hotpotqa",
        text="Alan Turing was an English mathematician, computer scientist, and cryptanalyst. During the Second World War, Turing worked for the Government Code and Cypher School at Bletchley Park, where he devised the Bombe electromechanical machine to decipher German Enigma messages.",
        metadata={"title": "Alan Turing at Bletchley Park", "source": "HotpotQA-Science"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_004",
        domain="hotpotqa",
        text="Bletchley Park is an English country house and estate in Milton Keynes, Buckinghamshire, that served as the central site for Allied codebreakers during World War II. Historians estimate its intelligence work shortened the war in Europe by two to four years.",
        metadata={"title": "Bletchley Park Estate", "source": "HotpotQA-History"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_005",
        domain="hotpotqa",
        text="Mount Everest is Earth's highest mountain above sea level at 8,848.86 metres (29,031.7 ft), located in the Mahalangur Himal sub-range of the Himalayas. The international border between China (Tibet Autonomous Region) and Nepal runs directly across its summit point.",
        metadata={"title": "Mount Everest Geography", "source": "HotpotQA-Geography"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_006",
        domain="hotpotqa",
        text="Sir Edmund Hillary of New Zealand and Tenzing Norgay, a Sherpa mountaineer from Nepal, were the first climbers confirmed to have reached the summit of Mount Everest on 29 May 1953 as part of the ninth British expedition led by John Hunt.",
        metadata={"title": "1953 Everest Expedition", "source": "HotpotQA-Geography"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_007",
        domain="hotpotqa",
        text="Photosynthesis is the biochemical process used by photoautotrophs such as plants, algae, and cyanobacteria to convert light energy into chemical energy stored in glucose molecules, releasing molecular oxygen as a byproduct of water photolysis.",
        metadata={"title": "Photosynthesis Biochemistry", "source": "HotpotQA-Biology"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_008",
        domain="hotpotqa",
        text="Chloroplasts are double-membrane plant cell organelles that conduct photosynthesis. Inside their thylakoid membranes, the pigment chlorophyll absorbs light energy to synthesize ATP and NADPH for the Calvin cycle in the stroma.",
        metadata={"title": "Chloroplast Organelle Structure", "source": "HotpotQA-Biology"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_009",
        domain="hotpotqa",
        text="James Cameron is a Canadian filmmaker born in Kapuskasing, Ontario, best known for directing the epic romance disaster film Titanic (1997), which won eleven Academy Awards including Best Picture and Best Director, as well as Avatar (2009).",
        metadata={"title": "James Cameron Filmography", "source": "HotpotQA-Arts"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_010",
        domain="hotpotqa",
        text="The RMS Titanic was a British Olympic-class ocean liner operated by the White Star Line that sank in the North Atlantic Ocean on 15 April 1912 after striking an iceberg during her maiden voyage from Southampton to New York City.",
        metadata={"title": "RMS Titanic Maiden Voyage", "source": "HotpotQA-History"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_011",
        domain="hotpotqa",
        text="Marie Skłodowska Curie was a Polish and naturalized-French physicist and chemist who conducted pioneering research on radioactivity. She was the first person to win two Nobel Prizes in different scientific fields: Physics in 1903 and Chemistry in 1911 for isolating radium and polonium.",
        metadata={"title": "Marie Curie Nobel Prizes", "source": "HotpotQA-Science"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_012",
        domain="hotpotqa",
        text="The 1903 Nobel Prize in Physics was jointly awarded to Henri Becquerel for his discovery of spontaneous radioactivity and to Pierre and Marie Curie for their joint radiation phenomena investigations.",
        metadata={"title": "1903 Physics Nobel Laureates", "source": "HotpotQA-Science"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_013",
        domain="hotpotqa",
        text="The Panama Canal is an artificial 82-kilometre (51-mile) waterway in Panama that connects the Atlantic Ocean with the Pacific Ocean via the Isthmus of Panama, using a system of locks to raise ships to Gatun Lake at 26 metres above sea level.",
        metadata={"title": "Panama Canal Engineering", "source": "HotpotQA-Geography"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_014",
        domain="hotpotqa",
        text="France began work on the Panama Canal in 1881 under Ferdinand de Lesseps, builder of the Suez Canal, but abandoned the project due to tropical diseases and engineering failures before the United States took over in 1904 and opened it on 15 August 1914.",
        metadata={"title": "Panama Canal Construction History", "source": "HotpotQA-History"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_015",
        domain="hotpotqa",
        text="CRISPR-Cas9 is a genome-editing technology adapted from a naturally occurring bacterial immune defense system. Emmanuelle Charpentier and Jennifer Doudna were awarded the 2020 Nobel Prize in Chemistry for developing the programmable RNA-guided DNA cleavage method.",
        metadata={"title": "CRISPR-Cas9 Genome Editing", "source": "HotpotQA-Biology"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_016",
        domain="hotpotqa",
        text="The Apollo 11 mission launched atop a Saturn V rocket from Kennedy Space Center on July 16, 1969. Commander Neil Armstrong and Lunar Module Pilot Buzz Aldrin landed the Apollo Lunar Module Eagle on July 20, 1969, while Michael Collins orbited above in Command Module Columbia.",
        metadata={"title": "Apollo 11 Lunar Landing", "source": "HotpotQA-Science"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_017",
        domain="hotpotqa",
        text="The Saturn V was an American human-rated expendable super heavy-lift launch vehicle developed by NASA under the direction of Wernher von Braun at the Marshall Space Flight Center in Huntsville, Alabama.",
        metadata={"title": "Saturn V Rocket Development", "source": "HotpotQA-Science"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_018",
        domain="hotpotqa",
        text="The Treaty of Versailles was the primary peace treaty that brought World War I to an end, signed on 28 June 1919 in the Hall of Mirrors at the Palace of Versailles exactly five years after the assassination of Archduke Franz Ferdinand.",
        metadata={"title": "Treaty of Versailles 1919", "source": "HotpotQA-History"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_019",
        domain="hotpotqa",
        text="The Bretton Woods Conference, formally known as the United Nations Monetary and Financial Conference, gathered 730 delegates from 44 Allied nations at the Mount Washington Hotel in Bretton Woods, New Hampshire, in July 1944, establishing the IMF and World Bank.",
        metadata={"title": "Bretton Woods Conference", "source": "HotpotQA-Economics"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_020",
        domain="hotpotqa",
        text="John Maynard Keynes led the British delegation at the 1944 Bretton Woods Conference and proposed an international clearing union with a supranational currency called the Bancor, though the conference ultimately adopted Harry Dexter White's U.S. dollar-anchored plan.",
        metadata={"title": "Keynes and the Bancor Proposal", "source": "HotpotQA-Economics"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_021",
        domain="hotpotqa",
        text="The James Webb Space Telescope (JWST) is an infrared space observatory launched on 25 December 2021 on an Ariane 5 rocket from Kourou, French Guiana, operating in a halo orbit around the Sun-Earth L2 Lagrange point approximately 1.5 million kilometres from Earth.",
        metadata={"title": "James Webb Space Telescope Orbit", "source": "HotpotQA-Astronomy"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_022",
        domain="hotpotqa",
        text="Unlike the Hubble Space Telescope, which orbits Earth in low Earth orbit at roughly 540 km altitude and observes primarily in ultraviolet and visible light, the James Webb Space Telescope uses a 6.5-metre gold-coated beryllium primary mirror optimized for infrared astronomy.",
        metadata={"title": "Hubble vs JWST Mirror Design", "source": "HotpotQA-Astronomy"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_023",
        domain="hotpotqa",
        text="Penicillin was discovered in September 1928 by Scottish physician and microbiologist Alexander Fleming at St Mary's Hospital in London when he observed that a mold contaminant, Penicillium notatum, inhibited the growth of Staphylococcus bacteria.",
        metadata={"title": "Discovery of Penicillin", "source": "HotpotQA-Medicine"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_024",
        domain="hotpotqa",
        text="Howard Florey and Ernst Chain at the University of Oxford purified penicillin and demonstrated its therapeutic efficacy in 1940, sharing the 1945 Nobel Prize in Physiology or Medicine with Alexander Fleming for mass-producible antibiotic treatment.",
        metadata={"title": "Purification of Penicillin at Oxford", "source": "HotpotQA-Medicine"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_025",
        domain="hotpotqa",
        text="The Gutenberg Bible, printed by Johannes Gutenberg in Mainz, Germany, in the 1450s using movable metal type, marked the start of the Printing Revolution in Europe. Surviving complete copies contain 1,282 pages bound in two volumes of 42 lines per column.",
        metadata={"title": "Gutenberg 42-Line Bible", "source": "HotpotQA-History"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_026",
        domain="hotpotqa",
        text="The Mariana Trench is an oceanic trench located in the western Pacific Ocean about 200 kilometres east of the Mariana Islands. Its deepest known point, the Challenger Deep, reaches a depth of approximately 10,935 metres (35,876 ft).",
        metadata={"title": "Mariana Trench Challenger Deep", "source": "HotpotQA-Geography"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_027",
        domain="hotpotqa",
        text="Swiss oceanographer Jacques Piccard and U.S. Navy Lieutenant Don Walsh made the first crewed descent to the bottom of the Challenger Deep in the Mariana Trench on 23 January 1960 aboard the bathyscaphe Trieste.",
        metadata={"title": "Bathyscaphe Trieste 1960 Descent", "source": "HotpotQA-Geography"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_028",
        domain="hotpotqa",
        text="The Turing Award, officially the ACM A.M. Turing Award, is an annual prize given by the Association for Computing Machinery for contributions of lasting technical importance to computer science, first awarded in 1966 to Alan Perlis for compiler construction.",
        metadata={"title": "ACM A.M. Turing Award", "source": "HotpotQA-ComputerScience"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_029",
        domain="hotpotqa",
        text="Geoffrey Hinton, Yoshua Bengio, and Yann LeCun received the 2018 ACM A.M. Turing Award for conceptual and engineering breakthroughs that made deep neural networks and backpropagation a critical component of modern computing.",
        metadata={"title": "2018 Turing Award Deep Learning", "source": "HotpotQA-ComputerScience"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_030",
        domain="hotpotqa",
        text="The Silk Road was a network of Eurasian trade routes active from the second century BCE under the Han dynasty of China until the mid-15th century, connecting Chang'an (Xi'an) with the Mediterranean Sea and facilitating exchange of silk, spices, paper, and Buddhism.",
        metadata={"title": "Silk Road Eurasian Trade Network", "source": "HotpotQA-History"}
    )
]

# Corpus definition for Legal Text (Dense Contracts, Clauses, and Jurisdictional Statutes - 30 passages)
LEGAL_CORPUS = [
    DocumentChunk(
        chunk_id="leg_chunk_001",
        domain="legal",
        text="Section 8.1 (Limitation of Liability Cap): In no event shall either party's aggregate cumulative liability arising out of or related to this Agreement exceed the total subscription fees actually paid by Customer to Vendor hereunder in the twelve (12) months immediately preceding the event giving rise to liability.",
        metadata={"clause_type": "Limitation of Liability", "source": "Master Services Agreement"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_002",
        domain="legal",
        text="Section 8.2 (Exclusion of Consequential Damages): Neither party shall be liable under any legal or equitable theory for any lost profits, loss of revenue, loss of data, loss of goodwill, or indirect, special, incidental, exemplary, punitive, or consequential damages, even if advised of the possibility of such damages.",
        metadata={"clause_type": "Consequential Damages", "source": "Master Services Agreement"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_003",
        domain="legal",
        text="Section 11.4 (Governing Law and Exclusive Venue): This Agreement shall be governed by and construed in accordance with the domestic laws of the State of Delaware, without giving effect to any choice or conflict of law provision. Any legal suit or proceeding shall be instituted exclusively in the state or federal courts located in New Castle County, Delaware.",
        metadata={"clause_type": "Choice of Law", "source": "Commercial Contract"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_004",
        domain="legal",
        text="Section 4.3 (Confidentiality Obligations and Survival): The Receiving Party agrees to hold all Confidential Information in strict confidence using at least the same degree of care it uses to protect its own proprietary information of like importance, but no less than reasonable care, for a survival period of five (5) years following expiration or termination.",
        metadata={"clause_type": "Confidentiality", "source": "Non-Disclosure Agreement"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_005",
        domain="legal",
        text="Section 14.1 (Force Majeure Excuse): Neither party shall be liable for any delay or failure in performance (excluding payment obligations) to the extent caused by circumstances beyond its reasonable control, including acts of God, earthquakes, pandemics, war, terrorism, embargoes, labor strikes, or national telecommunications grid failures.",
        metadata={"clause_type": "Force Majeure", "source": "Supply Agreement"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_006",
        domain="legal",
        text="Section 9.3 (Intellectual Property Indemnification): Vendor shall defend Customer at Vendor's expense against any third-party claim, suit, or proceeding alleging that Customer's authorized use of the Licensed Software directly infringes any valid United States patent, copyright, or registered trademark, and shall indemnify Customer for damages and reasonable attorneys' fees finally awarded.",
        metadata={"clause_type": "IP Indemnity", "source": "Software License Agreement"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_007",
        domain="legal",
        text="Section 12.2 (Termination for Material Breach and Cure Period): Either party may terminate this Agreement for cause upon thirty (30) days' prior written notice to the other party if the other party materially breaches any material covenant or obligation hereunder and fails to cure such breach within said thirty (30) day notice period.",
        metadata={"clause_type": "Termination for Cause", "source": "Service Agreement"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_008",
        domain="legal",
        text="Article 17 (GDPR Right to Erasure / Right to be Forgotten): The data subject shall have the right to obtain from the controller the erasure of personal data concerning him or her without undue delay, and within no more than thirty (30) calendar days, where the personal data are no longer necessary in relation to the purposes for which they were collected.",
        metadata={"clause_type": "Data Privacy", "source": "EU GDPR Regulation"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_009",
        domain="legal",
        text="Section 3.2 (Invoicing, Payment Net Terms, and Late Interest): Customer shall pay all undisputed invoiced amounts in U.S. Dollars within thirty (30) days of the invoice date (Net 30). Any overdue undisputed balance shall accrue late interest at the lesser of 1.5% per month (18% per annum) or the highest rate permitted by applicable usury law.",
        metadata={"clause_type": "Payment Terms", "source": "Commercial Terms"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_010",
        domain="legal",
        text="Section 6.1 (Disclaimer of Implied Warranties): Except for the express limited warranties set forth in Section 6.0, the SaaS Platform and Deliverables are provided strictly 'AS IS' and 'AS AVAILABLE', and Vendor expressly disclaims all implied warranties of merchantability, fitness for a particular purpose, title, and non-infringement.",
        metadata={"clause_type": "Warranty Disclaimer", "source": "Software License Agreement"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_011",
        domain="legal",
        text="Section 15.2 (Binding Arbitration and Class Action Waiver): Any controversy or claim arising out of or relating to this Agreement shall be resolved by final and binding arbitration administered by the American Arbitration Association (AAA) under its Commercial Arbitration Rules before a panel of three (3) neutral arbitrators in New York, NY.",
        metadata={"clause_type": "Arbitration", "source": "Dispute Resolution Addendum"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_012",
        domain="legal",
        text="Section 7.4 (Data Breach Notification Timeline): In the event of a confirmed Security Incident resulting in unauthorized access to Customer Personal Data, Data Processor shall notify Data Controller without undue delay and in no event later than seventy-two (72) hours after becoming aware of the breach.",
        metadata={"clause_type": "Data Breach Notice", "source": "Data Processing Addendum"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_013",
        domain="legal",
        text="Section 5.1 (Service Level Agreement Uptime Commitment): Vendor warrants that the Production Cloud Service will maintain a Monthly Uptime Percentage of at least 99.9% during each calendar month, excluding scheduled maintenance windows announced at least forty-eight (48) hours in advance.",
        metadata={"clause_type": "SLA Uptime", "source": "Service Level Agreement"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_014",
        domain="legal",
        text="Section 5.2 (SLA Service Credits Remedy): If Monthly Uptime falls below 99.9% but remains at or above 99.0%, Customer shall be eligible to receive a Service Credit equal to ten percent (10%) of the monthly recurring fee; if below 99.0%, a twenty-five percent (25%) Service Credit shall apply as Customer's sole and exclusive remedy.",
        metadata={"clause_type": "SLA Credits", "source": "Service Level Agreement"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_015",
        domain="legal",
        text="Section 13.1 (Anti-Assignment and Change of Control): Neither party may assign, delegate, or transfer this Agreement or any of its rights or obligations hereunder without the prior written consent of the other party, except that either party may assign this Agreement in its entirety to a successor in connection with a merger or acquisition of substantially all assets.",
        metadata={"clause_type": "Assignment", "source": "Master Services Agreement"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_016",
        domain="legal",
        text="Section 10.2 (Non-Solicitation of Employees): During the Term of this Agreement and for twelve (12) months thereafter, neither party shall directly or indirectly solicit for employment or hire any technical or managerial employee of the other party who was materially involved in the performance of Services, excluding general public job postings.",
        metadata={"clause_type": "Non-Solicitation", "source": "Consulting Agreement"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_017",
        domain="legal",
        text="Section 2.4 (Work Made for Hire and IP Ownership): All custom deliverables, source code modifications, and inventions conceived specifically for Customer under an executed Statement of Work shall be deemed 'works made for hire' and shall vest exclusively in Customer upon full payment of all applicable fees.",
        metadata={"clause_type": "IP Ownership", "source": "Professional Services SOW"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_018",
        domain="legal",
        text="Section 2.5 (Vendor Pre-Existing Background IP License): Notwithstanding Section 2.4, Vendor retains sole ownership of all Pre-Existing Intellectual Property, developer tools, and generic software libraries, granting Customer a non-exclusive, perpetual, worldwide, royalty-free license to use such Background IP solely as embedded in the Deliverables.",
        metadata={"clause_type": "Background IP", "source": "Professional Services SOW"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_019",
        domain="legal",
        text="Section 16.1 (Financial and Compliance Audit Rights): Upon at least fifteen (15) business days' prior written notice and no more than once per calendar year during normal business hours, Customer may engage an independent certified public accountant to audit Vendor's records solely to verify billing accuracy and SOC 2 security compliance.",
        metadata={"clause_type": "Audit Rights", "source": "Enterprise Addendum"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_020",
        domain="legal",
        text="Section 16.2 (Audit Cost Allocation): Customer shall bear all costs and expenses of any compliance or billing audit conducted under Section 16.1, unless the audit reveals an overcharge by Vendor exceeding five percent (5%) of the invoiced fees for the audited period, in which case Vendor shall reimburse Customer's reasonable audit costs.",
        metadata={"clause_type": "Audit Costs", "source": "Enterprise Addendum"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_021",
        domain="legal",
        text="Section 12.1 (Termination for Convenience): Customer may terminate an Order Form for convenience at any time by providing at least sixty (60) days' prior written notice to Vendor, provided that Customer shall remain liable for all fees accrued through the effective termination date and shall not be entitled to any refund of prepaid annual fees.",
        metadata={"clause_type": "Termination for Convenience", "source": "Service Agreement"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_022",
        domain="legal",
        text="Section 17.3 (Source Code Escrow Release Conditions): Vendor shall deposit encrypted source code for the Licensed Software with Iron Mountain Escrow. The escrow agent shall release the deposited source code to Customer only if Vendor files for Chapter 7 bankruptcy liquidation or ceases commercial support operations for more than forty-five (45) consecutive days.",
        metadata={"clause_type": "Source Code Escrow", "source": "Enterprise Software License"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_023",
        domain="legal",
        text="Section 18.1 (Mandatory Commercial Insurance Coverage): Throughout the Term, Vendor shall maintain at its sole expense Commercial General Liability insurance of at least $2,000,000 per occurrence and Cyber Liability / Errors & Omissions insurance of not less than $5,000,000 in the annual aggregate.",
        metadata={"clause_type": "Insurance Requirements", "source": "Vendor Risk Addendum"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_024",
        domain="legal",
        text="Section 8.3 (Super-Cap Exceptions to Liability Limitation): The liability cap in Section 8.1 shall not apply to (a) indemnification obligations under Section 9.3, (b) breaches of confidentiality under Section 4.3, or (c) gross negligence or willful misconduct, provided that liability for Data Protection breaches shall be subject to a separate super-cap of two times (2x) annual fees.",
        metadata={"clause_type": "Super-Cap Liability", "source": "Master Services Agreement"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_025",
        domain="legal",
        text="Section 7.8 (Subprocessor Authorization and Objection): Data Processor shall provide Data Controller with at least thirty (30) days' advance written notice before engaging any new third-party Subprocessor to process Personal Data, allowing Data Controller to object in writing on reasonable data protection grounds.",
        metadata={"clause_type": "Subprocessors", "source": "Data Processing Addendum"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_026",
        domain="legal",
        text="Section 19.2 (Severability and Reformation): If any provision of this Agreement is held by a court of competent jurisdiction to be invalid, void, or unenforceable, the remaining provisions shall continue in full force and effect, and the invalid provision shall be reformed to the minimum extent necessary to reflect the parties' original economic intent.",
        metadata={"clause_type": "Severability", "source": "General Provisions"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_027",
        domain="legal",
        text="Section 19.4 (Entire Agreement and Integration Clause): This Agreement, together with all executed Order Forms and Data Processing Addenda, constitutes the entire agreement between the parties and supersedes all prior oral or written proposals, negotiations, purchase order pre-printed terms, and communications.",
        metadata={"clause_type": "Entire Agreement", "source": "General Provisions"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_028",
        domain="legal",
        text="Section 12.5 (Post-Termination Data Retrieval and Deletion): Upon expiration or termination of this Agreement, Vendor shall make Customer Data available for export in standard JSON or CSV format for thirty (30) days, after which Vendor shall permanently delete and overwrite all Customer Data from production servers within sixty (60) days.",
        metadata={"clause_type": "Post-Termination Data", "source": "Master Services Agreement"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_029",
        domain="legal",
        text="Section 11.8 (Export Control and Sanctions Compliance): Each party represents that it is not named on any U.S. Treasury OFAC Specially Designated Nationals (SDN) list and shall not export or re-export the Software in violation of U.S. Export Administration Regulations (EAR) to any embargoed jurisdiction.",
        metadata={"clause_type": "Export Compliance", "source": "Regulatory Addendum"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_030",
        domain="legal",
        text="Section 3.5 (Annual Price Escalation Cap): Following the Initial Subscription Term, Vendor may increase annual subscription renewal fees no more than once per twelve-month renewal period by a percentage not to exceed the lesser of five percent (5%) or the year-over-year percentage increase in the U.S. Consumer Price Index (CPI-U).",
        metadata={"clause_type": "Price Escalation Cap", "source": "Commercial Terms"}
    )
]

# Corpus extracted from Extended_RAG_Grading_Comparison_Report
REPORT_CORPUS = [
    DocumentChunk(
        chunk_id="rep_chunk_001",
        domain="report",
        text="Comparative Evaluation of Relevance-Grading Strategies in Corrective Retrieval-Augmented Generation Systems. Extended Major Project Report - B.Tech CSE (AI/ML), Final Year. Retrieval-Augmented Generation (RAG) systems answer questions by retrieving relevant text from a document collection and passing it to a language model to generate an answer.",
        metadata={"section": "1. Introduction", "title": "Project Title and Overview"}
    ),
    DocumentChunk(
        chunk_id="rep_chunk_002",
        domain="report",
        text="Problem Statement: A known weakness of standard RAG pipelines is that they trust retrieval blindly: if the retrieved passages are irrelevant or incomplete, the model still generates a fluent, confident answer that may not be grounded in any real evidence (hallucination). Corrective RAG approaches address this by adding a grading step that checks whether retrieved evidence is actually relevant before answering, retrying the search when it is not.",
        metadata={"section": "1. Introduction", "title": "Problem Statement & RAG Weakness"}
    ),
    DocumentChunk(
        chunk_id="rep_chunk_003",
        domain="report",
        text="Motivation and Research Gap: Published techniques such as Self-RAG and Corrective RAG (CRAG) each introduce a grading mechanism and build their system around it, but neither work compares its chosen grading approach against realistic alternatives on cost, latency, and accuracy grounds. In practice, anyone deploying a corrective RAG system has to make this choice without a controlled study. This leaves an open question: does a full LLM-based relevance judgement actually outperform cheaper alternatives by enough to justify its cost, and does the answer depend on domain or question difficulty?",
        metadata={"section": "2. Motivation and Research Gap", "title": "Research Gap in Grading Strategies"}
    ),
    DocumentChunk(
        chunk_id="rep_chunk_004",
        domain="report",
        text="Objectives: 1) Reuse the base system - Retain and reuse the existing corrective RAG pipeline (retrieval, correction loop, generation) as the base system. 2) Implement multiple graders - Implement three interchangeable relevance-grading strategies under a single shared interface. 3) Build gold-standard labels - Construct a hand-labelled gold dataset of 120 query-chunk relevance judgements (60 HotpotQA, 60 Legal) to measure grading accuracy directly. 4) Evaluate across domains - Evaluate across HotpotQA and Legal text. 5) Validate statistically - Apply paired Student's t-test and paired bootstrap resampling with Holm-Bonferroni correction. 6) Deliver both a viva demo dashboard and a paper draft.",
        metadata={"section": "3. Objectives", "title": "Core Project Objectives"}
    ),
    DocumentChunk(
        chunk_id="rep_chunk_005",
        domain="report",
        text="The Three Grading Strategies Under Comparison: Strategy A - LLM-prompt judge: Local Ollama qwen2.5:3b is prompted directly with the query and a retrieved passage and asked to judge relevance (yes/no). Flexible, but slow and comparatively costly to run at scale. Strategy B - Cross-encoder / NLI model: Pretrained cross-encoder/ms-marco-MiniLM-L-6-v2 scores relevance directly without invoking a general-purpose LLM. Purpose-built, fast, free to run locally. Strategy C - Similarity threshold: No separate grading step at all - the raw cosine similarity score from all-MiniLM-L6-v2 retrieval is thresholded directly. Cheapest possible baseline.",
        metadata={"section": "4. The Three Grading Strategies", "title": "Grading Strategies A, B, and C"}
    ),
    DocumentChunk(
        chunk_id="rep_chunk_006",
        domain="report",
        text="Methodology and System Architecture: The underlying pipeline is unchanged from the original build: documents are chunked and embedded into a FAISS dense vector store; a query retrieves the top-k candidate chunks; the active grading strategy scores each chunk as relevant or not; if too few chunks are judged relevant, the query is automatically reformulated and retrieval is retried, up to a bounded number of attempts, after which a fallback response is returned. The grading step is implemented behind a single shared function signature so any strategy can be swapped in.",
        metadata={"section": "5. Methodology", "title": "Corrective Pipeline Architecture"}
    ),
    DocumentChunk(
        chunk_id="rep_chunk_007",
        domain="report",
        text="Evaluation Metrics and Statistical Validation: Grading accuracy against the 120-pair hand-labelled gold set (precision, recall, F1, specificity, accuracy of relevance decision). Downstream answer quality: Exact Match (EM) and token F1 against ground-truth answers. Latency per grading call and per end-to-end query. Retry rate: how often the correction loop is triggered. Cost proxy: number of LLM calls required per query. Differences between strategies are tested for statistical significance using paired Student's t-test and 2,000-iteration paired bootstrap resampling with Holm-Bonferroni correction.",
        metadata={"section": "5.3 - 5.4 Metrics and Validation", "title": "Evaluation Metrics and Statistical Tests"}
    ),
    DocumentChunk(
        chunk_id="rep_chunk_008",
        domain="report",
        text="Why This Constitutes a Genuine Research Contribution: The value of this study does not depend on any one grading strategy winning. If the cheapest method performs nearly as well as the most expensive one, that is a directly useful finding for deploying RAG under compute or cost constraints (Pareto frontier). If the LLM-based judge or Cross-Encoder clearly outperforms raw similarity thresholding on dense legal text, that justifies a dedicated grading step with empirical evidence rather than assumption.",
        metadata={"section": "6. Research Contribution", "title": "Pareto Frontier & Research Value"}
    ),
    DocumentChunk(
        chunk_id="rep_chunk_009",
        domain="report",
        text="Summary: How the Project Idea Evolved: Original idea was a single-strategy corrective RAG system with 1 LLM grader on 1 domain (HotpotQA) without gold labels. Extended project retains the same base pipeline but introduces 3 interchangeable grading strategies (LLM, Cross-Encoder, Similarity), 2 distinct domains (HotpotQA and Legal), a 120-pair hand-labelled gold benchmark, and paired t-test + bootstrap statistical validation, delivered with an interactive viva dashboard and research paper draft.",
        metadata={"section": "9. Project Evolution", "title": "Evolution from Original to Extended Project"}
    )
]


def load_initial_corpora():
    """Populates vector store with domain corpora and builds dense FAISS index matrices."""
    vector_store.set_chunks("hotpotqa", HOTPOTQA_CORPUS)
    vector_store.set_chunks("legal", LEGAL_CORPUS)
    vector_store.set_chunks("report", REPORT_CORPUS)


def load_gold_benchmark() -> List[GoldBenchmarkItem]:
    """Loads hand-labelled gold relevance benchmark dataset from gold_benchmark.json."""
    benchmark_path = os.path.join(os.path.dirname(__file__), "gold_benchmark.json")
    if os.path.exists(benchmark_path):
        with open(benchmark_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [GoldBenchmarkItem(**item) for item in data]
    return []


def save_gold_benchmark_item(item: GoldBenchmarkItem) -> List[GoldBenchmarkItem]:
    """Persists a new or updated hand-labelled query-chunk pair to gold_benchmark.json."""
    benchmark_path = os.path.join(os.path.dirname(__file__), "gold_benchmark.json")
    items = load_gold_benchmark()
    existing_idx = next((idx for idx, x in enumerate(items) if x.pair_id == item.pair_id), None)
    if existing_idx is not None:
        items[existing_idx] = item
    else:
        items.append(item)
    with open(benchmark_path, "w", encoding="utf-8") as f:
        json.dump([x.model_dump() for x in items], f, indent=2)
    return items
