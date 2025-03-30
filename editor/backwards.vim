" Language: Backwards
" Instructions:
" Move this file into .vim/syntax/backwards.vim or
" .config/nvim/syntax/backwards.vim
"
" in .vimrc, put
" autocmd BufRead,BufNewFile *.imp set filetype=backwards

if exists("b:current_syntax")
    finish
endif

syntax match Symbols /\v[|$+%-;.:=<>!&^()[\]{}*\/]/
syntax keyword Keywords nruter tnirp tel fi dne esle
syntax keyword TypeNames 821i 821u 821b
syntax match Number "\<\d\+\>\(\w\)\@!"
syntax keyword TrueFalse eurt eslaf

highlight link Keywords Keyword
highlight link Symbols Operator
highlight link TypeNames Type
highlight link Number Number
highlight link TrueFalse Function

let b:current_syntax = "backwards"
