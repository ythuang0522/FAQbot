import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any
from app.utils.logger import get_logger
from app.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class DatabaseService:
    def __init__(self, csv_path: Optional[str] = None):
        self.csv_path = csv_path or settings.database_csv_path
        self.df: Optional[pd.DataFrame] = None
        self.load_data()
    
    def load_data(self) -> None:
        """Load CSV data into memory with error handling."""
        try:
            csv_file = Path(self.csv_path)
            if not csv_file.exists():
                raise FileNotFoundError(f"Database CSV not found: {self.csv_path}")
            
            self.df = pd.read_csv(csv_file)
            self.validate_data()
            logger.info(f"Loaded {len(self.df)} organisms from database")
            
        except Exception as e:
            logger.error(f"Error loading database: {e}")
            raise
    
    def validate_data(self) -> None:
        """Validate CSV data structure."""
        required_columns = [
            'classification', 'nucleic_acid', 'organism_name', 
            'pneumonia_level', 'meningitis_level', 'bloodstream_level'
        ]
        
        missing_columns = [col for col in required_columns if col not in self.df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Validate classification values
        valid_classifications = ['bacteria', 'fungi', 'virus', 'parasite']
        invalid_classifications = self.df[~self.df['classification'].isin(valid_classifications)]
        if not invalid_classifications.empty:
            logger.warning(f"Invalid classifications found: {invalid_classifications['classification'].unique()}")
    
    def get_organism_statistics(
        self, 
        classification: Optional[str] = None,
        nucleic_acid: Optional[str] = None,
        infection_type: Optional[str] = None,
        pathogenic_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get statistics about organisms with flexible filtering.
        
        Args:
            classification: Filter by organism type (bacteria, fungi, virus, parasite)
            nucleic_acid: Filter by nucleic acid type (DNA, RNA) - only for viruses
            infection_type: Filter by infection type (pneumonia, meningitis, bloodstream)
            pathogenic_level: Filter by pathogenic level (H, M, L, W, D)
        
        Returns:
            Dictionary with count and breakdown statistics
        """
        try:
            filtered_df = self.df.copy()
            
            # Apply filters
            if classification:
                filtered_df = filtered_df[filtered_df['classification'] == classification]
            
            if nucleic_acid:
                filtered_df = filtered_df[filtered_df['nucleic_acid'] == nucleic_acid]
            
            if infection_type and pathogenic_level:
                column_map = {
                    'pneumonia': 'pneumonia_level',
                    'meningitis': 'meningitis_level', 
                    'bloodstream': 'bloodstream_level'
                }
                if infection_type in column_map:
                    column = column_map[infection_type]
                    filtered_df = filtered_df[filtered_df[column] == pathogenic_level]
            
            # Calculate statistics
            total_count = len(filtered_df)
            
            # Breakdown by classification
            classification_breakdown = filtered_df['classification'].value_counts().to_dict()
            
            # If filtering viruses, include nucleic acid breakdown
            nucleic_acid_breakdown = {}
            if classification == 'virus' or filtered_df['classification'].eq('virus').any():
                virus_df = filtered_df[filtered_df['classification'] == 'virus']
                nucleic_acid_breakdown = virus_df['nucleic_acid'].value_counts().to_dict()
            
            # Pathogenic level breakdown if infection type specified
            pathogenic_breakdown = {}
            if infection_type:
                column_map = {
                    'pneumonia': 'pneumonia_level',
                    'meningitis': 'meningitis_level',
                    'bloodstream': 'bloodstream_level'
                }
                if infection_type in column_map:
                    column = column_map[infection_type]
                    pathogenic_breakdown = filtered_df[column].value_counts().to_dict()
            
            result = {
                'total_count': total_count,
                'classification_breakdown': classification_breakdown,
                'filters_applied': {
                    'classification': classification,
                    'nucleic_acid': nucleic_acid,
                    'infection_type': infection_type,
                    'pathogenic_level': pathogenic_level
                }
            }
            
            if nucleic_acid_breakdown:
                result['nucleic_acid_breakdown'] = nucleic_acid_breakdown
            
            if pathogenic_breakdown:
                result['pathogenic_level_breakdown'] = pathogenic_breakdown
            
            logger.info(f"Database query returned {total_count} organisms with filters: {result['filters_applied']}")
            return result
            
        except Exception as e:
            logger.error(f"Error in get_organism_statistics: {e}")
            raise
    
    def search_and_list_organisms(
        self, 
        organism_name: Optional[str] = None,
        list_mode: bool = False,
        classification: Optional[str] = None,
        nucleic_acid: Optional[str] = None,
        infection_type: Optional[str] = None,
        pathogenic_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for a specific organism OR list organisms by criteria.
        
        Args:
            organism_name: Name of specific organism to search for
            list_mode: If True, return list of organisms instead of single organism
            classification: Filter by organism type (bacteria, fungi, virus, parasite)
            nucleic_acid: Filter viruses by nucleic acid (DNA/RNA)
            infection_type: Filter by infection type (pneumonia, meningitis, bloodstream)
            pathogenic_level: Filter by pathogenic level (H, M, L, W, D)
            
        Returns:
            Dictionary with organism details or list of organisms
        """
        try:
            if list_mode:
                # List mode: return filtered list of organisms
                return self._list_organisms_by_criteria(
                    classification=classification,
                    nucleic_acid=nucleic_acid,
                    infection_type=infection_type,
                    pathogenic_level=pathogenic_level
                )
            else:
                # Search mode: find specific organism
                if not organism_name:
                    raise ValueError("organism_name is required when list_mode=False")
                
                return self._search_single_organism(organism_name)
                
        except Exception as e:
            logger.error(f"Error in search_and_list_organisms: {e}")
            raise
    
    def _search_single_organism(self, organism_name: str) -> Dict[str, Any]:
        """Search for a single specific organism."""
        # Case-insensitive search
        organism_df = self.df[
            self.df['organism_name'].str.lower() == organism_name.lower()
        ]
        
        if organism_df.empty:
            logger.info(f"Organism not found: {organism_name}")
            return {
                'query_type': 'single_organism',
                'found': False,
                'searched_name': organism_name,
                'message': f"Organism '{organism_name}' not found in database"
            }
        
        # Get the first match (should be only one)
        organism_data = organism_df.iloc[0].to_dict()
        
        # Format the response
        result = {
            'query_type': 'single_organism',
            'found': True,
            'organism_name': organism_data['organism_name'],
            'classification': organism_data['classification'],
            'pathogenic_profile': {
                'pneumonia_level': organism_data['pneumonia_level'],
                'meningitis_level': organism_data['meningitis_level'],
                'bloodstream_level': organism_data['bloodstream_level']
            }
        }
        
        # Add nucleic acid info for viruses
        if organism_data['classification'] == 'virus':
            result['nucleic_acid'] = organism_data['nucleic_acid']
        
        logger.info(f"Found organism: {organism_name}")
        return result
    
    def _list_organisms_by_criteria(
        self,
        classification: Optional[str] = None,
        nucleic_acid: Optional[str] = None,
        infection_type: Optional[str] = None,
        pathogenic_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """List organisms matching the specified criteria."""
        filtered_df = self.df.copy()
        
        # Apply filters
        if classification:
            filtered_df = filtered_df[filtered_df['classification'] == classification]
        
        if nucleic_acid:
            filtered_df = filtered_df[filtered_df['nucleic_acid'] == nucleic_acid]
        
        if infection_type and pathogenic_level:
            column_map = {
                'pneumonia': 'pneumonia_level',
                'meningitis': 'meningitis_level',
                'bloodstream': 'bloodstream_level'
            }
            if infection_type in column_map:
                column = column_map[infection_type]
                filtered_df = filtered_df[filtered_df[column] == pathogenic_level]
        
        # Convert to list of organisms
        organisms_list = []
        for _, row in filtered_df.iterrows():
            organism_info = {
                'organism_name': row['organism_name'],
                'classification': row['classification'],
                'pathogenic_profile': {
                    'pneumonia_level': row['pneumonia_level'],
                    'meningitis_level': row['meningitis_level'],
                    'bloodstream_level': row['bloodstream_level']
                }
            }
            
            # Add nucleic acid for viruses
            if row['classification'] == 'virus':
                organism_info['nucleic_acid'] = row['nucleic_acid']
            
            organisms_list.append(organism_info)
        
        # Summary information
        total_count = len(organisms_list)
        classification_summary = filtered_df['classification'].value_counts().to_dict()
        
        # Build filter description
        applied_filters = []
        if classification:
            applied_filters.append(f"classification={classification}")
        if nucleic_acid:
            applied_filters.append(f"nucleic_acid={nucleic_acid}")
        if infection_type and pathogenic_level:
            applied_filters.append(f"{infection_type}_level={pathogenic_level}")
        
        filter_description = ", ".join(applied_filters) if applied_filters else "no filters"
        
        logger.info(f"Listed {total_count} organisms with filters: {filter_description}")
        
        return {
            'query_type': 'organism_list',
            'total_count': total_count,
            'filter_description': filter_description,
            'classification_summary': classification_summary,
            'organisms': organisms_list,
            'filters_applied': {
                'classification': classification,
                'nucleic_acid': nucleic_acid,
                'infection_type': infection_type,
                'pathogenic_level': pathogenic_level
            }
        }
    
    def get_total_organisms(self) -> int:
        """Get total number of organisms in database."""
        return len(self.df) if self.df is not None else 0
    
    def get_available_classifications(self) -> List[str]:
        """Get list of available organism classifications."""
        if self.df is None:
            return []
        return self.df['classification'].unique().tolist() 