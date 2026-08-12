# data_processor.py
import os
import pandas as pd
from pathlib import Path
import zipfile



import PyPDF2
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import Config

class NCERTDataProcessor:
    def __init__(self):
        self.data_dir = Path("./data")
        self.data_dir.mkdir(exist_ok=True)
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", ", ", " ", ""]
        )

    def download_kaggle_dataset(self):
        """Download NCERT books dataset from Kaggle"""
        print("Downloading NCERT dataset from Kaggle...")

        # Set up Kaggle credentials
        kaggle_dir = Path.home() / ".kaggle"
        kaggle_dir.mkdir(exist_ok=True)

        try:
            import kaggle
            kaggle.api.authenticate()
            kaggle.api.dataset_download_files(
                "adityasharma01/ncert-books",
                path=str(self.data_dir),
                unzip=True
            )
            print("Dataset downloaded successfully!")
            return True
        except Exception as e:
            print(f"Error downloading from Kaggle: {e}")
            print("\nManual download instructions:")
            print("1. Go to: [kaggle.com](https://www.kaggle.com/datasets/adityasharma01/ncert-books)")
            print("2. Download the dataset")
            print("3. Extract to ./data folder")
            return False

    def extract_text_from_pdf(self, pdf_path):
        """Extract text from a PDF file"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
        except Exception as e:
            print(f"Error reading {pdf_path}: {e}")
        return text

    def clean_text(self, text):
        """Clean and preprocess extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove page numbers and headers
        text = re.sub(r'\b\d{1,3}\s*CHEMISTRY\b', '', text, flags=re.IGNORECASE)
        # Remove special characters but keep chemical formulas
        text = re.sub(r'[^\w\s\.\,\;\:\-\+\=\(\)\[\]\{\}\/\°\%\$]', '', text)
        return text.strip()

    def is_chemistry_content(self, text):
        """Check if text contains JEE Chemistry relevant content"""
        chemistry_keywords = [
            'atom', 'molecule', 'element', 'compound', 'reaction', 'bond',
            'electron', 'proton', 'neutron', 'orbital', 'valence', 'ion',
            'acid', 'base', 'salt', 'oxidation', 'reduction', 'equilibrium',
            'mole', 'molarity', 'concentration', 'pH', 'pOH', 'buffer',
            'organic', 'inorganic', 'hydrocarbon', 'functional group',
            'polymer', 'metal', 'nonmetal', 'periodic', 'thermodynamic',
            'enthalpy', 'entropy', 'gibbs', 'kinetic', 'catalyst'
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in chemistry_keywords)

    def process_chemistry_data(self):
        """Process all chemistry-related content from the dataset"""
        all_chunks = []

        # Look for PDF files in the data directory
        pdf_files = list(self.data_dir.rglob("*.pdf"))

        # Filter for chemistry-related files
        chemistry_keywords = ['chemistry', 'chem', 'class 11', 'class 12', 'xi', 'xii']
        chemistry_pdfs = [
            f for f in pdf_files
            if any(kw in f.name.lower() for kw in chemistry_keywords)
        ]

        if not chemistry_pdfs:
            print("No chemistry PDFs found. Processing all available PDFs...")
            chemistry_pdfs = pdf_files

        print(f"Found {len(chemistry_pdfs)} files to process")

        for pdf_path in chemistry_pdfs:
            print(f"Processing: {pdf_path.name}")

            # Extract text
            text = self.extract_text_from_pdf(pdf_path)
            if not text:
                continue

            # Clean text
            cleaned_text = self.clean_text(text)

            # Create chunks
            chunks = self.splitter.split_text(cleaned_text)

            # Filter for chemistry-relevant chunks
            for chunk in chunks:
                if self.is_chemistry_content(chunk) and len(chunk) > 100:
                    all_chunks.append({
                        "text": chunk,
                        "source": pdf_path.name,
                        "type": "ncert_chemistry"
                    })

        print(f"Created {len(all_chunks)} chemistry-relevant chunks")
        return all_chunks

    def create_sample_chemistry_data(self):
        """Create sample JEE Chemistry data if Kaggle download fails"""
        print("Creating sample JEE Chemistry dataset...")

        sample_content = [
            # Atomic Structure
            """Atomic Structure and Quantum Mechanics:\n            The atom consists of a nucleus containing protons and neutrons, surrounded by electrons in orbitals.\n            Bohr's model: E = -13.6 × Z²/n² eV for hydrogen-like atoms.\n            Quantum numbers: n (principal), l (azimuthal), m (magnetic), s (spin).\n            Aufbau principle: Electrons fill orbitals in order of increasing energy.\n            Hund's rule: Electrons occupy degenerate orbitals singly before pairing.\n            Pauli exclusion principle: No two electrons can have identical quantum numbers.""",

            # Chemical Bonding
            """Chemical Bonding and Molecular Structure:\n            Ionic bonding occurs between metals and nonmetals through electron transfer.\n            Covalent bonding involves sharing of electrons between atoms.\n            Hybridization: sp (linear, 180°), sp² (trigonal planar, 120°), sp³ (tetrahedral, 109.5°).\n            VSEPR theory predicts molecular geometry based on electron pair repulsion.\n            Molecular orbital theory: σ and π bonds, bonding and antibonding orbitals.\n            Bond order = (bonding electrons - antibonding electrons) / 2.""",

            # Thermodynamics
            """Thermodynamics in Chemistry:\n            First law: ΔU = q + w, where U is internal energy, q is heat, w is work.\n            Enthalpy: H = U + PV, ΔH = qp at constant pressure.\n            Hess's Law: Enthalpy change is independent of the path taken.\n            Gibbs free energy: ΔG = ΔH - TΔS. Spontaneous if ΔG < 0.\n            Standard enthalpy of formation: ΔHf° for elements in standard state = 0.\n            Bond enthalpy: Energy required to break one mole of bonds in gaseous state.""",

            # Equilibrium
            """Chemical Equilibrium:\n            Law of mass action: Kc = [products]^n / [reactors]^m at equilibrium.\n            Le Chatelier's principle: System shifts to counteract applied stress.\n            Relation between Kp and Kc: Kp = Kc(RT)^Δn.\n            Ionic product of water: Kw = [H⁺][OH⁻] = 10⁻¹⁴ at 25°C.\n            pH = -log[H⁺], pOH = -log[OH⁻], pH + pOH = 14.\n            Buffer solutions resist pH changes; Henderson-Hasselbalch equation applies.""",

            # Electrochemistry
            """Electrochemistry:\n            Nernst equation: E = E° - (RT/nF)ln(Q) or E = E° - (0.059/n)log(Q) at 25°C.\n            Faraday's laws: m = ZIt, where Z = M/nF (electrochemical equivalent).\n            Standard electrode potential: Measured against SHE (Standard Hydrogen Electrode).\n            Galvanic cell: Spontaneous redox reaction, ΔG < 0, E°cell > 0.\n            Electrolytic cell: Non-spontaneous, requires external EMF.\n            Conductivity: κ = 1/ρ, Molar conductivity: Λm = κ × 1000/M.""",

            # Organic Chemistry - Basics
            """Organic Chemistry Fundamentals:\n            Hybridization determines geometry: sp³ (tetrahedral), sp² (planar), sp (linear).\n            Inductive effect: Electron-withdrawing (-I) or donating (+I) through sigma bonds.\n            Resonance: Delocalization of π electrons, increases stability.\n            Hyperconjugation: σ-π conjugation, explains stability of carbocations.\n            Types of reagents: Electrophiles (electron-seeking), Nucleophiles (nucleus-seeking).\n            Reaction intermediates: Carbocations, carbanions, free radicals, carbenes.""",

            # Organic Reactions
            """Organic Reaction Mechanisms:\n            SN1: Unimolecular, two-step, carbocation intermediate, racemization.\n            SN2: Bimolecular, one-step, Walden inversion, backside attack.\n            E1: Unimolecular elimination, carbocation intermediate.\n            E2: Bimolecular elimination, anti-periplanar geometry required.\n            Addition reactions: Markovnikov's rule for unsymmetrical alkenes.k\n            Electrophilic aromatic substitution: Friedel-Crafts, nitration, halogenation.""",

            # Coordination Chemistry
            """Coordination Compounds:\n            Werner's theory: Primary valence (oxidation state), Secondary valence (coordination number).\n            Nomenclature: Ligands alphabetically, then metal with oxidation state in Roman numerals.\n            Isomerism: Geometrical (cis-trans), optical, linkage, coordination, ionization.\n            Crystal Field Theory: d-orbital splitting, CFSE calculations.\n            Spectrochemical series: I⁻ < Br⁻ < Cl⁻ < F⁻ < OH⁻ < H₂O < NH₃ < en < NO₂⁻ < CN⁻ < CO.\n            Magnetic properties: High spin vs low spin complexes.""",

            # Chemical Kinetics
            """Chemical Kinetics:\n            Rate = k[A]^m[B]^n, order = m + n, molecularity = number of molecules in elementary step.\n            Zero order: [A] = [A]₀ - kt, t½ = [A]₀/2k.\n            First order: ln[A] = ln[A]₀ - kt, t½ = 0.693/k (independent of concentration).\n            Arrhenius equation: k = Ae^(-Ea/RT), ln(k₂/k₁) = (Ea/R)(1/T₁ - 1/T₂).\n            Collision theory: Effective collisions require minimum energy and proper orientation.\n            Catalyst lowers activation energy, doesn't change equilibrium.""",

            # P-Block Elements
            """P-Block Elements for JEE:\n            Group 15: Nitrogen family - NH₃, HNO₃ preparation and properties.\n            Group 16: Oxygen family - Allotropy of sulfur, H₂SO₄ manufacture (Contact process).\n            Group 17: Halogens - Oxidizing power decreases down the group.\n            Group 18: Noble gases - Compounds of xenon (XeF₂, XeF₄, XeF₆).\n            Interhalogen compounds: ClF₃, BrF₅ - structures and hybridization.\n            Oxyacids of halogens: Acidic strength increases with oxidation state.""",
        ]

        all_chunks = []
        for i, content in enumerate(sample_content):
            chunks = self.splitter.split_text(content)
            for chunk in chunks:
                all_chunks.append({
                    "text": chunk,
                    "source": f"jee_chemistry_sample_{i+1}",
                    "type": "jee_chemistry"
                })

        print(f"Created {len(all_chunks)} sample chunks")
        return all_chunks


def main():
    processor = NCERTDataProcessor()

    # Try to download from Kaggle
    if processor.download_kaggle_dataset():
        chunks = processor.process_chemistry_data()
    else:
        # Fall back to sample data
        chunks = processor.create_sample_chemistry_data()

    return chunks


if __name__ == "__main__":
    chunks = main()
    print(f"Total chunks ready for vector DB: {len(chunks)}")
