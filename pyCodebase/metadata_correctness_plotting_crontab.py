from config import *
from utils import *
from workflow import *
from plots import *

import sys
import re
import pandas as pd
import seaborn as sns
import time
import plotnine
import matplotlib.pyplot as plt
from collections import OrderedDict
import numpy as np
import gspread

import os
import json
from google.oauth2 import service_account
import gspread

# Google API configuration
GOOGLE_API_CONFIG = {
    'credentials_variable': 'GOOGLE_SERVICE_ACCOUNT',
    'scopes': ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
}

def initialize_google_sheets2():
    """
    Initializes and returns a Google Sheets client authorized with OAuth2 credentials.

    This function reads the service account environment variable, converts it into a Credentials object,
    and uses it to authorize a gspread client.

    Returns:
        gspread.client.Client: An authorized Google Sheets client instance.
    """
    # Load the token.json file
    creds = service_account.Credentials.from_service_account_info(json.loads(os.environ[GOOGLE_API_CONFIG['credentials_variable']]), scopes=GOOGLE_API_CONFIG['scopes'])
    # Use the credentials to authorize gspread
    gc = gspread.authorize(creds)
    return gc

from google.oauth2.credentials import Credentials
import os

gc = initialize_google_sheets2()

credentials = authenticate_with_google(
    GOOGLE_API_CONFIG['scopes'],
    GOOGLE_API_CONFIG['credentials_variable']
)

# The .json key you downloaded
#credentials_file = "/home/kkimler/gca_crontab/OAuth_kk_metadata_uploader2.json"

## Specify which Google API we are using - Spreadsheets and Drive
#scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

# To access GDrive, we authenticate python with GDrive, which creates an updated credentials object which we can use for the rest of the script
#credentials = authenticate_with_google(scopes, credentials_file)

folder_id = '1tT6R2WhOok-_gXRU7O0OudKDNVl44w4O'

# Then list the google sheets in that folder
googlesheets = list_google_sheets(credentials, folder_id)

# remove example sheet
name_to_remove = "HCA_Tier_1_Example_Metadata"
googlesheets = [d for d in googlesheets if d['name'] != name_to_remove]

metadata = load_sheets_metadata(credentials, googlesheets)

def collect_columns(data, columns):
    if isinstance(data, dict):
        for key, value in data.items():
            collect_columns(value, columns)
    elif isinstance(data, pd.DataFrame):
        for column in data.columns:
            columns.add(column)

def get_unique_columns(nested_data):
    columns = set()
    collect_columns(nested_data, columns)
    return columns

unique_columns = get_unique_columns(metadata)
print(unique_columns)

# Permitted data & column importance

# Library
#----------
# Tier 1 - must
allowed_reference_genome = ['GRCh38', 'GRCh37', 'GRCm39', 'GRCm38', 'GRCm37', 'not_applicable']
allowed_sequenced_fragment = ["3'", "5'", "full-length", "probe-based"]
# Tier 1 - recommended
allowed_intron_inclusion = ['yes', 'no'] # important for single-cell and nucleus integration, therefore we ask for this specifically
allowed_doublet_detection = ['none', 'manual', 'doublet_finder', 'scrublet', 'doublet_decon']
allowed_ambient_count_correction = ['none','cellbender','decontX','soupX']
allowed_sequencing_platform = ['Illumina', 'ONT', 'PacBio']
allowed_assay_ontology_term = [
    "10x 3' v1", "10x 3' v2", "10x 3' v3", "10x 3' v4",
    "10x 5' v1", "10x 5' v2", "10x 5' v3",
    "Standard Drop-seq",
    "inDrop v1", "inDrop v2",
    "Smart-seq", "Smart-seq2", "Smart-seq3",
    "Seq-Well S3",
    "CEL-seq", "CEL-seq2",
    "MARS-seq", "MARS-seq2"
]


# CellxGene
#----------
# allowed_disease_ontology_term_id = ['PATO:0000461'] # This is the Tier1 requirement, but we need this as part of tier2 for analysis 
# allowed_development_stage_ontology_term_id = ['unknown'] # This is the Tier1 requirement, but we need this as part of tier2 for analysis 
allowed_self_reported_ethnicity_ontology_term_id = ['unknown'] # no ethnicity allowed in tier 1


# Donor
#----------
# Tier 1 - must
allowed_organism_ontology_term_id = ['NCBITaxon:9606'] # h. sapiens
allowed_manner_of_death = ['not_applicable', 'unknown', '0', '1', '2', '3', '4'] # see configs  #TODO!! change not applicable
allowed_sex_ontology_term_id = ['PATO:0000383', 'PATO:0000384'] #F, M


# Sample
#----------
# Tier 1 - must
allowed_tissue_ontology_term = ['duodenum', 'jejunum', 'ileum',
                                'ascending_colon', 'hepatic_flexure', 'transverse_colon', 'splenic_flexure', 'descending_colon',
                                'sigmoid_colon', 'rectum', 'anal_canal',
                                'small_intestine', 'colon', 'caecum',
                                'gastrointestinal_system_mesentery', 'vermiform_appendix', 'mesenteric_lymph_node'
                               ]
allowed_tissue_ontology_term_id = ['UBERON:0002114','UBERON:0002115','UBERON:0002116',
                                  'UBERON:0001156','UBERON:0022277', 'UBERON:0001157','UBERON:0022276', 'UBERON:0001158',
                                  'UBERON:0001159','UBERON:0001052','UBERON:0000159',
                                  'UBERON:0002108','UBERON:0001155', 'UBERON:0001153',
                                  'UBERON:0004854', 'UBERON:0001154','UBERON:0002509',
                                  ]
allowed_sample_source = ["surgical_donor", "postmortem_donor", "organ_donor"]
allowed_sample_collection_method = ['biopsy', 'surgical_resection', 'brush', 'scraping', 'blood_draw', 'body_fluid', 'other']
allowed_tissue_type = ["tissue", "organoid", "cell_culture"]
allowed_sample_site_condition = ["healthy", "diseased", "adjacent"]
allowed_sample_preservation_method = ['fresh', 'frozen']
allowed_suspension_type = ['cell', 'nucleus', 'na']
allowed_is_primary_data = ['FALSE', 'TRUE']

# Tier 1 - recommended

# Other tier2 metadata we need for downstream analysis
allowed_radial_tissue_term = ['EPI', 'LP', 'MUSC', 'EPI_LP' ,'LP_MUSC', 'EPI_LP_MUSC', 'MLN']
allowed_age_range = ['unknown', '0-1', '1-4', '0-9', '5-14', '10-19', '15-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80-89', '90-99', '100-']
allowed_development_stage_ontology_term_id = ['HsapDv:0000261','HsapDv:0000265','HsapDv:0000271','HsapDv:0000268',
                                             'HsapDv:0000237','HsapDv:0000238','HsapDv:0000239','HsapDv:0000240',
                                             'HsapDv:0000241','HsapDv:0000242','HsapDv:0000243','HsapDv:0000244',
                                             'HsapDv:0000247'] # Tier1 requirement is "unknown", but we need this as part of tier2 for analysis 


allowed_closest_GCA_celltype = [
    "Epithelial",
    "Enterocytes",
    "Early Enterocytes",
    "Late Enterocytes",
    "BEST4+ Cells",
    "Colonocytes",
    "Early Colonocytes",
    "Late Colonocytes",
    "Laminin colonocytes",
    "BEST4+ Colonocytes",
    "Follicle associated enterocyte (FAE)",
    "Epithelial Stem Cells (LGR5+)",
    "Enteroendocrine Cells (EEC)",
    "EEC Progenitor",
    "I Cells (CCK+)",
    "S Cells (SCT+)",
    "Mo Cells (MLN+)",
    "Enterochromaffin Cells",
    "L Cells (PYY+)",
    "K Cells (GIP+)",
    "D Cells (SST+)",
    "N Cells",
    "Gastric Enteroendocrine Cells",
    "G Cells",
    "Enterochromaffin-like Cells (ECL Cells)",
    "D Cells (Gastric)",
    "Paneth Cells",
    "Tuft Cells",
    "Goblet Cells",
    "Mature goblet cells",
    "Microfold Cells (M Cells)",
    "Transiently Amplifying Cells (TA)",
    "Cycling TA Cells",
    "Secretory TA Cells",
    "Absorptive TA Cells",
    "Stromal",
    "Endothelial",
    "Arteriolar Endothelial",
    "Capillary Endothelial",
    "Post arteriole capillary (PAC)",
    "Pre venule capillary (PVC)",
    "Venular Endothelial",
    "Lymphatic Endothelial",
    "Lacteals",
    "Mesothelial",
    "Fibroblasts",
    "Subepithelial fibroblasts (S2)",
    "Crypt Top (S2B)",
    "Crypt Bottom (S2A)",
    "Lamina propria fibroblasts (S1)",
    "Submucosal Fibroblasts (S3)",
    "mLTo Cells (mesenchymal lymphoid tissue organizer cells)",
    "Fibroblastic reticular cells",
    "Follicular Dendritic Cells (fDC)",
    "Subserosal Fibroblasts",
    "Muscularis Propria Fibroblasts",
    "Myofibroblasts",
    "Interstitial Cells of Cajal (ICC)",
    "Pericytes",
    "Angiogenic Pericytes",
    "Contractile Pericytes",
    "Immature Pericytes",
    "Secretory Pericyte",
    "Glia",
    "Differentiating Glia",
    "Progenitor Glia",
    "Intra-Ganglionic Glia",
    "Myenteric Plexus Glia /Type I",
    "Submucosal Plexus Glia / Type I",
    "Extra-Ganglionic Glia",
    "Mucosal/Type III",
    "Muscularis propria/Type IV",
    "Smooth Muscle Cells (SMC)",
    "Outer Muscle Cells",
    "Inner Muscle Cells",
    "Adipocytes",
    "Immune",
    "Lymphoid",
    "B Cell Lineage",
    "Plasma Cells",
    "IGA.IGK",
    "IGA.IGL",
    "IGE",
    "IGG",
    "IGM",
    "Germinal Center B Cells (GC)",
    "Dark Zone",
    "Light Zone",
    "Memory B Cells",
    "Naive B-Cells",
    "Atypical B-Cells",
    "Marginal zone B cell (MZB)",
    "Cycling B cell",
    "T Cells",
    "CD4+ T-Cells",
    "Tfh",
    "Th1",
    "Th17",
    "Th2",
    "Treg",
    "Naive T-Cells",
    "CD8+ T-Cells",
    "Effector/Memory CD8+ T-Cells",
    "Circulating Effector/Memory CD8+ T-Cells",
    "Memory/Exhausted CD8+ T-Cells",
    "TRM CD8+ T-Cells",
    "IEL CD8+ T-Cells",
    "Naive CD8+ T-Cells",
    "Tc17 CD8+ T-Cells",
    "Unconventional T-Cells",
    "Vδ1+ Gamma-Delta",
    "Vδ2+ Gamma-Delta",
    "Vδ3+ Gamma-Delta",
    "MAIT",
    "NK T Cells",
    "Cycling T Cells",
    "Treg Cycling",
    "Activated T Cells",
    "ILC",
    "NK Cells",
    "ILC1",
    "ILC2",
    "ILC3",
    "ILC Progenitor",
    "Myeloid",
    "Monocytes",
    "Macrophages",
    "Cycling Macrophages",
    "Tissue Resident Macrophages",
    "M2 Macrophages",
    "M1 Macrophages",
    "Dendritic Cells",
    "migDC",
    "cDC1",
    "cDC2",
    "pDC",
    "Monocyte derived dendritic cell (MO DC)",
    "Granulocytes",
    "Mast Cells",
    "Neutrophils",
    "Basophils",
    "Eosinophils",
    "Megakaryocytes",
    "Red Blood Cells (RBC)",
    "Neurons",
    "Excitory Neurons",
    "Inhibitory Neurons",
    "Neuroendocrine Neurons"
]


# since we're searching global vars for allowed_
# don't name anything else with allowed_, so we call this "permitted_" hah
permitted_values_dict = {
    name.split('_', 1)[1]: value  # this removes the "allowed_"
    for name, value in globals().items() # yep we can search through our python env vars to make this
    if name.startswith('allowed_') and isinstance(value, list) # boom, here's our dict
}

# again, permitted instead of allowed, nice alliteration
permitted_patterns_dict = {
    # Dataset
    'title':r'^.{1,}$', # tier1(uns) - must
    'study_pi':r'^.{1,}$', #r'^[A-Za-z]+,[a-zA-Z0-9-]+$', # tier1(uns) - must
    'doi': r'^10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$', # tier1(uns) - must  # should be publication_doi
    'contact_email': r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', # tier1(uns) - must
    'description':r'^.{1,}$', # tier1(uns) - must
    'consortia':r'^.{1,}$', # tier1(uns) - must
    'cell_type_ontology_term_id':r'^CL:\d{7}$', # tier1(uns) - must

    # Library
    'gene_annotation_version':r'^.{1,}$', # tier1(uns) - must - so far non-empty, but needs to be ensembl version or NCBI/RefSeq ID (e.g. v110; GCF_000001405.40)
    'alignment_software': r'(starsolo|cellranger|kallisto_bustools|GSNAP)_[0-9]+(\.[0-9a-zA-Z]+)*', # tier1(uns) - must - here we allow cellranger, kallisto_bustools, or starsolo, or GSNAP versions
    'library_id':r'^.{1,}$', # tier1(uns) - must
    
    # Donor
    'donor_id':r'^.{1,}$', # tier1(uns) - must
    'sample_collection_site': r'^[A-Za-z_]+$', # alphabetical only, tier1(uns) - recommended
    'sample_collection_relative_time_point': r'^[A-Za-z0-9-.+-]+_[a-zA-Z0-9-.+-]+$', # alphanumeric + _- with _ delimiter (HCA pref), tier1(uns) - recommended
    'disease_ontology_term_id': r'^(MONDO:\d{7}|PATO:0000461)$',  # Tier1 must is 'PATO:0000461' (see above) - here Tier2 and CellxGene metadata data definition, to add human phenotype terms: HP:\d{7}|
    
    # Sample
    'sample_id':r'^.{1,}$', # tier1(uns) - must
    'institute':r'^.{1,}$', # tier1(uns) - must  # currently in data set tab, but should be sample tab in excel sheet as data can be generated at multiple sites
    'cell_enrichment': r'^CL:\d{7}$', # tier1(uns) - must
    'assay_ontology_term_id': r'^EFO:\d{7}$', # tier1(uns) - must
    'library_preparation_batch':r'^.{1,}$', # tier1(uns) - must
    'library_sequencing_run':r'^.{1,}$',  # tier1(uns) - must
    'dissociation_protocol':r'^.{1,}$',  # tier1 - gut specific
    #'tissue_free_text':r'^.+$', # tier1(uns) - recommended
    
    # Celltype
    'author_celltype':r'^(?!n/a$).*'
}


# column names with comment were in comparison to the HCA Tier 1 reference

meta_col_dict = {
    'title': 'MUST',
    'dataset_id': 'MUST',
    'study_pi': 'MUST',
    'batch_condition': 'RECOMMENDED',
    'default_embedding': 'RECOMMENDED',
    'comments': 'RECOMMENDED',
    'sample_id': 'MUST',
    'donor_id': 'MUST',
    'protocol_url': 'RECOMMENDED',
    'institute': 'MUST',
    'sample_collection_site': 'RECOMMENDED',
    'sample_collection_relative_time_point': 'RECOMMENDED',
    'library_id': 'MUST', 
    'library_id_repository': 'RECOMMENDED',
    'author_batch_notes': 'RECOMMENDED',
    'organism_ontology_term_id': 'MUST',
    'manner_of_death': 'MUST',
    'sample_source': 'MUST',
    'sex_ontology_term': 'RECOMMENDED',
    'sex_ontology_term_id': 'MUST',
    'sample_collection_method': 'MUST',
    'tissue_type': 'MUST',
    'sampled_site_condition': 'MUST',
    'tissue_ontology_term_id': 'MUST',
    'tissue_ontology_term': 'RECOMMENDED',
    'tissue_free_text': 'RECOMMENDED',
    'sample_preservation_method': 'MUST',
    'suspension_type': 'MUST',
    'cell_enrichment': 'MUST',
    'cell_viability_percentage': 'RECOMMENDED',
    'cell_number_loaded': 'RECOMMENDED',
    'sample_collection_year': 'RECOMMENDED',
    'assay_ontology_term_id': 'MUST',
    'library_preparation_batch': 'MUST',
    'library_sequencing_run': 'MUST',
    'sequenced_fragment': 'MUST',
    'sequencing_platform': 'RECOMMENDED',
    'is_primary_data': 'MUST',
    'reference_genome': 'MUST',
    'gene_annotation_version': 'MUST',
    'alignment_software': 'MUST',
    'intron_inclusion': 'RECOMMENDED',
    'doublet_detection': 'RECOMMENDED',
    'author_cell_type': 'RECOMMENDED',
    'cell_type_ontology_term_id': 'MUST',
    'disease_ontology_term_id': 'MUST',
    'self_reported_ethnicity_ontology_term_id': 'MUST',
    'consortia': 'MUST',
    'description': 'MUST',
    'contact_email': 'MUST', #'contact name_email': 'MUST',
    'publication_doi': 'MUST',
    'development_stage_ontology_term_id': 'MUST', # CellxGene -> Tier2
    'author_celltype': 'MUST',
    'closest_GCA_celltype': 'RECOMMENDED',
    
    'age_range': 'GUTSPECIFIC',
    'disease_free_text': 'GUTSPECIFIC',
    'radial_tissue_term': 'GUTSPECIFIC', # Added -> Tier2
    'dissociation_protocol': 'GUTSPECIFIC'
    
    
}

print('creating plots...')
df_dataset = metadata['tier 1 dataset']
df_donor = metadata['tier 1 donor']
df_sample = metadata['tier 1 sample']
df_celltype = metadata['tier 1 celltype']

def validate_column(df, col, allowed_values=None, pattern=None):
    if allowed_values:
        return df[col].apply(lambda x: x in allowed_values).mean()
    elif pattern:
        return df[col].astype(str).apply(lambda x: bool(re.match(pattern, x))).mean()
    else:
        return pd.notna(df[col]).mean()

from matplotlib.colors import LinearSegmentedColormap


def plot_data_correctness_heatmap2(df, title, meta_col_dict, permitted_values_dict, permitted_patterns_dict):
    data = []
    column_categories = []
    for col in df.columns:
        if col in meta_col_dict and col != 'worksheet':
            allowed_values = permitted_values_dict.get(col)
            pattern = permitted_patterns_dict.get(col)
            data.append(df.groupby('worksheet')[col].apply(lambda x: validate_column(x.to_frame(name=col), col, allowed_values, pattern)))
            column_categories.append(meta_col_dict.get(col, 'OPTIONAL'))
    if data:
        data = pd.concat(data, axis=1)
        categories = ['MUST', 'RECOMMENDED', 'OPTIONAL', 'GUTSPECIFIC']
        category_col_dict = {category: [] for category in categories}
        for col_name, category in zip(data.columns, column_categories):
            category_col_dict[category].append(col_name)
        columns_with_spaces = []
        category_positions = []
        col_position = 0
        for idx, category in enumerate(categories):
            cols_in_category = category_col_dict.get(category, [])
            if cols_in_category:
                category_positions.append((col_position, category, len(cols_in_category)))
                columns_with_spaces.extend(cols_in_category)
                col_position += len(cols_in_category)
                if idx < len(categories) - 1:
                    columns_with_spaces.append('')
                    col_position += 1
        for col in columns_with_spaces:
            if col == '':
                data[col] = np.nan
        data_for_plot = data[columns_with_spaces]
        block_width = 0.5
        block_height = 0.5
        fig_width = data_for_plot.shape[1] * block_width + 2
        fig_height = data_for_plot.shape[0] * block_height + 2
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        lighter_cmap = LinearSegmentedColormap.from_list("lighter_RdYlGn", ['#FF5C5C', '#ffffcc', '#ccffcc'])
        x_tick_labels = [col if col != '' else '' for col in data_for_plot.columns]
        data_values = data_for_plot.values
        annot_array = np.vectorize(lambda v: '' if np.isnan(v) else f'{v*100:.0f}%')(data_values)
        mesh = ax.pcolormesh(data_values, cmap=lighter_cmap, edgecolors='white', linewidth=0.1, vmin=0, vmax=1)
        for i in range(data_values.shape[0]):
            for j in range(data_values.shape[1]):
                value = annot_array[i, j]
                if value:
                    ax.text(j + 0.5, i + 0.5, value, ha='center', va='center', color='black', fontsize=6)
        ax.set_xticks(np.arange(data_values.shape[1]) + 0.5)
        ax.set_xticklabels(x_tick_labels, rotation=45, ha='right', fontsize=8)
        ax.set_yticks(np.arange(data_values.shape[0]) + 0.5)
        ax.set_yticklabels(data_for_plot.index, fontsize=8)
        plt.subplots_adjust(left=0.2, bottom=0.2, right=0.9, top=0.85)
        for pos, category, width in category_positions:
            ax.annotate(category, xy=(pos + width / 2, data_for_plot.shape[0] + 0.5), xytext=(0, 10), textcoords='offset points', ha='center', va='center', fontsize=8, fontweight='bold', annotation_clip=False)
        plt.title(f'{title} Metadata Correctness', fontsize=10)
        plt.tight_layout()
        # plt.show()
        filename = f"{title}_correctness_heatmap.png"
        plt.savefig(filename)
        plt.close()

print("saving plots")

plot_data_correctness_heatmap2(df_dataset, 'Dataset', meta_col_dict, permitted_values_dict, permitted_patterns_dict)
plot_data_correctness_heatmap2(df_donor, 'Donor', meta_col_dict, permitted_values_dict, permitted_patterns_dict)
plot_data_correctness_heatmap2(df_sample, 'Sample', meta_col_dict, permitted_values_dict, permitted_patterns_dict)
plot_data_correctness_heatmap2(df_celltype, 'Celltype', meta_col_dict, permitted_values_dict, permitted_patterns_dict)

print("plots saved")

