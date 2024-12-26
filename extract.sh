output_file="output.txt"

> "$output_file"

find . -type f -name "*.py" | while IFS= read -r file; do
    echo "===== $file =====" >> "$output_file"

    cat "$file" >> "$output_file"

    echo -e "\n" >> "$output_file"
done

echo "文件已提取到 $output_file"
