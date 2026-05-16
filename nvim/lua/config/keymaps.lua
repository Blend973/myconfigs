-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here
local map = vim.keymap.set
-- Ctrl+Backspace: delete word before cursor
map("i", "<C-BS>", "<C-w>", { desc = "Delete word before cursor" })
-- Ctrl+Delete: delete word after cursor
map("i", "<C-Del>", "<C-o>dw", { desc = "Delete word after cursor" })
-- Ctrl-C to copy (yank visual selection to system clipboard)
map("v", "<C-c>", '"+y', { desc = "Copy to system clipboard" })
-- Ctrl-V to paste in insert mode
map("i", "<C-v>", "<C-r>+", { desc = "Paste from system clipboard" })
map("n", "<leader>a", "ggVG")
