function ytf -d "Search and play YouTube videos"
    # Check dependencies
    for dep in yt-dlp jq fzf mpv
        if not type -q $dep
            echo "Error: '$dep' is not installed."
            return 1
        end
    end

    argparse --name=ytf 'h/help' 'a/audio' 'p/autoplay' -- $argv
    or return

    if set -q _flag_h
        echo "Usage: ytf [options] <search query>"
        echo "Options:"
        echo "  -a, --audio:    Audio only mode"
        echo "  -p, --autoplay: Autoplay related videos (Mix)"
        echo "  -h, --help:     Show this help"
        return
    end

    set -l query "$argv"

    # If no arguments are given, prompt for the initial search query
    if test -z "$query"
        read -P "Enter search query: " query
    end

    # Loop as long as the query is not empty
    while test -n "$query"
        echo "Searching for '$query'..."
        
        # Get Title, URL, and ID separated by tabs (\t)
        # Using flat-playlist ensures we get results quickly without downloading metadata
        set -l search_results (yt-dlp --flat-playlist -j "ytsearch50:$query" \
            | jq -r '"\(.title)\t\(.webpage_url)\t\(.id)"')

        if test -z "$search_results"
            echo "No results found for '$query'."
        else
            # Inner loop to select from the same search results
            while true
                # FZF Logic:
                # 1. We extract the ID (field 3)
                # 2. We construct the thumbnail URL
                # 3. We curl the image and pipe it to chafa (or kitten icat)
                set -l selected_line (printf "%s\n" $search_results | fzf --reverse \
                    --delimiter='\t' \
                    --with-nth='1' \
                    --preview 'set -l id (echo {} | cut -f3);
                              printf "%*s\n" 28 ""
                              curl -s "https://img.youtube.com/vi/$id/hqdefault.jpg" | \
                              chafa -f kitty \
                              -s {$FZF_PREVIEW_COLUMNS}x{$FZF_PREVIEW_LINES} \
                              --animate=false \
                              -' \
                    --preview-window=right:40%:wrap)

                if test -z "$selected_line"
                    # User cancelled fzf, break inner loop to start a new search
                    break
                end

                # Parse the selected line
                set -l parts (string split \t -- "$selected_line")
                set -l video_title $parts[1]
                set -l video_url $parts[2]
                set -l video_id $parts[3]

                echo "Playing: $video_title"

                set -l mpv_format "bestvideo[height<=720]+bestaudio/best[height<=720]"
                if set -q _flag_a
                    set mpv_format "bestaudio/best"
                end

                set -l final_url "$video_url"
                set -l mpv_opts 
                
                if set -q _flag_p
                    # For autoplay, construct YouTube's "mix" playlist URL
                    set final_url "https://www.youtube.com/watch?v=$video_id&list=RD$video_id"
                    # MPV needs to know it's handling a playlist now
                    set mpv_opts --ytdl-raw-options=yes-playlist=
                end

                # Run MPV
                # We detach slightly so the script loop stays responsive, 
                # but usually, we want to wait for MPV to finish to pick the next song.
                mpv --ytdl-format="$mpv_format" $mpv_opts "$final_url"
            end
        end

        # Prompt for a new search query.
        echo # New line for cleanliness
        read -P "Enter new search query (or press Enter to quit): " query
    end
end
