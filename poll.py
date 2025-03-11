import re
import argparse
from datetime import datetime
import os
from weasyprint import HTML

def extract_polls(file_path, target_date=None):
    """
    Extract polls from a WhatsApp chat export file.
    
    Args:
        file_path (str): Path to the WhatsApp chat export file
        target_date (str, optional): Date in DD/MM/YYYY format to filter polls
    
    Returns:
        list: List of polls found for the target date
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    poll_pattern = r'\[(\d{2}/\d{2}/\d{4}), (\d{2}:\d{2}:\d{2})\] .*?\u200ePOLL:(.*?)(?=\[\d{2}/\d{2}/\d{4}, \d{2}:\d{2}:\d{2}\]|$)'
    
    polls = []
    for poll_match in re.finditer(poll_pattern, content, re.DOTALL):
        date, time, poll_content = poll_match.groups()
        
        if target_date and date != target_date:
            continue
        
        question_lines = [line.strip() for line in poll_content.split('\n') if line.strip() and '\u200eOPTION:' not in line]
        question = '\n'.join(question_lines)
        
        options = {}
        option_pattern = r'\u200eOPTION: (.*?) \((\d+) votes?\)'
        for option_match in re.finditer(option_pattern, poll_content):
            option, votes = option_match.groups()
            options[option.strip()] = int(votes)
        
        polls.append({
            'date': date,
            'time': time,
            'question': question.strip(),
            'options': options
        })
    
    return polls

def format_html_summary(polls, date=None):
    date_str = f" for {date}" if date else ""
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Poll Summary{date_str}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .rtl {{ direction: rtl; text-align: right; }}
        .poll {{ border: 1px solid #ccc; margin: 10px 0; padding: 15px; border-radius: 5px; }}
        .winner {{ color: #2c7be5; font-weight: bold; }}
        .options {{ margin-left: 20px; }}
        .poll-time {{ font-size: 0.8em; color: #666; }}
        .total-votes {{ font-style: italic; color: #666; margin-bottom: 10px; }}
        h1 {{ color: #333; }}
    </style>
</head>
<body>
    <h1>Poll Summary{date_str}</h1>
"""
    
    if not polls:
        html += "<p>No polls found.</p>"
    else:
        for i, poll in enumerate(polls, 1):
            question = poll['question']
            options = poll['options']
            time = poll.get('time', '')
            
            html += f'<div class="poll">\n'
            html += f'    <h2>Poll {i} <span class="poll-time">({time})</span></h2>\n'
            html += f'    <h2 class="rtl">{question}</h2>\n'
            
            total_votes = sum(options.values())
            html += f'    <p class="total-votes">Total votes: {total_votes}</p>\n'
            
            sorted_options = sorted(options.items(), key=lambda x: x[1], reverse=True)
            
            if total_votes > 0:
                winner = sorted_options[0][0]
                html += f'    <p class="winner">Winner: <span class="rtl">{winner}</span> with {sorted_options[0][1]} votes</p>\n'
            
            html += '    <h3>Options:</h3>\n'
            html += '    <ul class="options">\n'
            for option, votes in sorted_options:
                percentage = (votes / total_votes * 100) if total_votes > 0 else 0
                html += f'        <li><span class="rtl">{option}</span>: {votes} votes ({percentage:.1f}%)</li>\n'
            html += '    </ul>\n'
            html += '</div>\n'
    
    html += """</body>
</html>"""
    return html

def generate_pdf(html_content, output_path):
    """
    Generate a PDF file from HTML content using WeasyPrint.
    """
    try:
        HTML(string=html_content).write_pdf(output_path)
        return True
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Extract and summarize WhatsApp polls')
    parser.add_argument('file', help='Path to WhatsApp chat export file')
    parser.add_argument('--date', help='Date to filter polls (DD/MM/YYYY format)')
    parser.add_argument('--pdf', help='Output PDF file for the summary')
    
    args = parser.parse_args()
    
    polls = extract_polls(args.file, args.date)
    html_content = format_html_summary(polls, args.date)
    
    if args.pdf:
        success = generate_pdf(html_content, args.pdf)
        if success:
            print(f"PDF summary written to {args.pdf}")
    else:
        print(html_content)

if __name__ == "__main__":
    main()
