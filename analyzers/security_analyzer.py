# analyzers/security_analyzer.py - Security header and vulnerability analysis

import pandas as pd
from typing import Dict, List
from urllib.parse import urlparse


class SecurityAnalyzer:
    """Analyzes security-related headers and potential vulnerabilities."""
    
    # Required security headers
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'HSTS - Forces HTTPS connections',
        'Content-Security-Policy': 'CSP - Prevents XSS attacks',
        'X-Frame-Options': 'Prevents clickjacking',
        'X-Content-Type-Options': 'Prevents MIME sniffing',
        'X-XSS-Protection': 'XSS filter (legacy)',
        'Referrer-Policy': 'Controls referrer information',
        'Permissions-Policy': 'Controls browser features'
    }
    
    @staticmethod
    def analyze_security(df: pd.DataFrame) -> Dict:
        """
        Analyze security aspects of HAR data.
        
        Note: HAR files may not always include response headers.
        This analysis focuses on URL patterns and protocol usage.
        
        Args:
            df: DataFrame with HAR entries
            
        Returns:
            Dictionary with security analysis
        """
        if df.empty:
            return {
                'security_score': 0,
                'issues': [],
                'recommendations': []
            }
        
        issues = []
        recommendations = []
        score = 100
        
        # Check for insecure protocols
        http_requests = df[df['url'].str.startswith('http://', na=False)]
        if not http_requests.empty:
            http_count = len(http_requests)
            http_percentage = (http_count / len(df) * 100)
            
            issues.append({
                'severity': 'High',
                'category': 'Insecure Protocol',
                'description': f'{http_count} requests ({http_percentage:.1f}%) use HTTP instead of HTTPS',
                'impact': 'Data transmitted in plain text, vulnerable to interception'
            })
            
            recommendations.append({
                'priority': 'High',
                'title': 'Migrate to HTTPS',
                'description': f'Convert {http_count} HTTP requests to HTTPS to encrypt data in transit'
            })
            
            score -= min(30, http_percentage)
        
        # Check for mixed content
        mixed_content = SecurityAnalyzer._check_mixed_content(df)
        if mixed_content['has_mixed_content']:
            issues.append({
                'severity': 'High',
                'category': 'Mixed Content',
                'description': f"Found {mixed_content['count']} HTTP resources on HTTPS pages",
                'impact': 'Browsers may block mixed content, breaking functionality'
            })
            
            recommendations.append({
                'priority': 'High',
                'title': 'Fix Mixed Content',
                'description': 'Update HTTP resources to HTTPS on secure pages'
            })
            
            score -= 20
        
        # Check for third-party security risks
        third_party_risks = SecurityAnalyzer._check_third_party_risks(df)
        if third_party_risks['high_risk_count'] > 0:
            issues.append({
                'severity': 'Medium',
                'category': 'Third-Party Risk',
                'description': f"{third_party_risks['high_risk_count']} requests to potentially risky third-party domains",
                'impact': 'Third-party scripts can access sensitive data'
            })
            
            score -= 10
        
        # Check for outdated libraries (based on URL patterns)
        outdated = SecurityAnalyzer._check_outdated_libraries(df)
        if outdated:
            issues.append({
                'severity': 'Medium',
                'category': 'Outdated Libraries',
                'description': f'Detected {len(outdated)} potentially outdated library versions',
                'impact': 'Known vulnerabilities may exist'
            })
            
            recommendations.append({
                'priority': 'Medium',
                'title': 'Update Libraries',
                'description': 'Review and update outdated libraries to latest secure versions'
            })
            
            score -= 15
        
        # Ensure score is between 0 and 100
        score = max(0, min(100, score))
        
        # Calculate grade
        grade = SecurityAnalyzer._calculate_grade(score)
        
        return {
            'security_score': score,
            'grade': grade,
            'issues': issues,
            'recommendations': recommendations,
            'http_requests': len(http_requests),
            'https_requests': len(df) - len(http_requests),
            'mixed_content': mixed_content,
            'third_party_risks': third_party_risks
        }
    
    @staticmethod
    def _check_mixed_content(df: pd.DataFrame) -> Dict:
        """Check for mixed content (HTTP resources on HTTPS pages)."""
        # Detect if main page is HTTPS
        https_requests = df[df['url'].str.startswith('https://', na=False)]
        http_requests = df[df['url'].str.startswith('http://', na=False)]
        
        # If we have both HTTPS and HTTP, we likely have mixed content
        has_mixed = len(https_requests) > 0 and len(http_requests) > 0
        
        return {
            'has_mixed_content': has_mixed,
            'count': len(http_requests) if has_mixed else 0,
            'http_urls': http_requests['url'].tolist() if has_mixed else []
        }
    
    @staticmethod
    def _check_third_party_risks(df: pd.DataFrame) -> Dict:
        """Check for third-party security risks."""
        # Get main domain
        if df.empty:
            return {'high_risk_count': 0, 'domains': []}
        
        df['domain'] = df['url'].apply(lambda x: urlparse(x).netloc)
        main_domain = df['domain'].value_counts().index[0] if not df.empty else ''
        
        # Identify third-party domains
        third_party = df[~df['domain'].str.contains(main_domain, na=False, regex=False)]
        
        # Check for tracking/analytics domains (potential privacy risks)
        tracking_patterns = [
            'google-analytics', 'googletagmanager', 'facebook.com/tr',
            'doubleclick', 'analytics', 'tracking', 'pixel'
        ]
        
        high_risk = third_party[
            third_party['url'].str.contains('|'.join(tracking_patterns), case=False, na=False, regex=True)
        ]
        
        return {
            'high_risk_count': len(high_risk),
            'domains': high_risk['domain'].unique().tolist()
        }
    
    @staticmethod
    def _check_outdated_libraries(df: pd.DataFrame) -> List[Dict]:
        """Check for outdated library versions based on URL patterns."""
        outdated = []
        
        # Common library patterns with known old versions
        library_patterns = {
            'jquery': r'jquery[/-]([0-9.]+)',
            'bootstrap': r'bootstrap[/-]([0-9.]+)',
            'angular': r'angular[/-]([0-9.]+)',
            'react': r'react[/-]([0-9.]+)',
            'vue': r'vue[/-]([0-9.]+)'
        }
        
        for library, pattern in library_patterns.items():
            # Use str.contains without capture groups for filtering
            filter_pattern = pattern.replace('([0-9.]+)', '[0-9.]+')
            matches = df[df['url'].str.contains(filter_pattern, case=False, na=False, regex=True)]
            
            if not matches.empty:
                # Extract version (simplified - would need more robust parsing in production)
                for url in matches['url']:
                    outdated.append({
                        'library': library,
                        'url': url
                    })
        
        return outdated
    
    @staticmethod
    def _calculate_grade(score: int) -> str:
        """Convert security score to letter grade."""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    @staticmethod
    def get_security_recommendations(df: pd.DataFrame) -> List[Dict]:
        """Get prioritized security recommendations."""
        analysis = SecurityAnalyzer.analyze_security(df)
        return analysis['recommendations']
    
    @staticmethod
    def get_protocol_breakdown(df: pd.DataFrame) -> Dict:
        """Get breakdown of HTTP vs HTTPS requests."""
        http_count = len(df[df['url'].str.startswith('http://', na=False)])
        https_count = len(df[df['url'].str.startswith('https://', na=False)])
        total = len(df)
        
        return {
            'http_count': http_count,
            'https_count': https_count,
            'http_percentage': round((http_count / total * 100) if total > 0 else 0, 2),
            'https_percentage': round((https_count / total * 100) if total > 0 else 0, 2),
            'total': total
        }
